from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import require_authenticated, require_permission
from app.db.session import get_db_session
from app.models import ModuloERP, Usuario
from app.schemas.modules import ModuleRead, ModuleStatusUpdate
from app.services.auth import add_audit_log

router = APIRouter(
    prefix="/api/modules",
    tags=["modules"],
    dependencies=[Depends(require_authenticated)],
)


@router.get("", response_model=list[ModuleRead])
def list_modules(db: Session = Depends(get_db_session)) -> list[ModuleRead]:
    modules = db.scalars(
        select(ModuloERP).order_by(ModuloERP.ordem, ModuloERP.nome)
    ).all()
    return [ModuleRead.model_validate(module) for module in modules]


@router.patch(
    "/{module_code}",
    response_model=ModuleRead,
    dependencies=[Depends(require_permission("settings:write"))],
)
def update_module(
    module_code: str,
    payload: ModuleStatusUpdate,
    db: Session = Depends(get_db_session),
    actor: Usuario | None = Depends(require_permission("settings:write")),
) -> ModuleRead:
    module = db.scalar(select(ModuloERP).where(ModuloERP.codigo == module_code))
    if module is None:
        raise HTTPException(status_code=404, detail="Módulo não encontrado.")
    module.ativo = payload.ativo
    add_audit_log(
        db,
        user_id=actor.id if actor else None,
        action="module_updated",
        entity="modulo_erp",
        entity_id=module.id,
        metadata={"codigo": module.codigo, "ativo": module.ativo},
    )
    db.commit()
    db.refresh(module)
    return ModuleRead.model_validate(module)
