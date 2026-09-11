from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import require_permission
from app.db.session import get_db_session
from app.models import Funcionario, Usuario
from app.schemas.auth import UsuarioCreate, UsuarioRead, UsuarioUpdate
from app.services.auth import add_audit_log, hash_password

router = APIRouter(prefix="/api/users", tags=["users"])


def _user_read(user: Usuario) -> UsuarioRead:
    return UsuarioRead.model_validate(user)


def _ensure_employee(db: Session, employee_id: int | None) -> None:
    if employee_id is not None and db.get(Funcionario, employee_id) is None:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado.")


@router.get("", response_model=list[UsuarioRead])
def list_users(
    db: Session = Depends(get_db_session),
    _: Usuario | None = Depends(require_permission("users:manage")),
) -> list[UsuarioRead]:
    users = db.scalars(select(Usuario).order_by(Usuario.id)).all()
    return [_user_read(user) for user in users]


@router.post("", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UsuarioCreate,
    db: Session = Depends(get_db_session),
    actor: Usuario | None = Depends(require_permission("users:manage")),
) -> UsuarioRead:
    _ensure_employee(db, payload.funcionario_id)
    user = Usuario(
        nome=payload.nome,
        email=payload.email,
        senha_hash=hash_password(payload.senha),
        role=payload.role,
        funcionario_id=payload.funcionario_id,
    )
    db.add(user)
    try:
        db.flush()
        add_audit_log(
            db,
            user_id=actor.id if actor else None,
            action="user_created",
            entity="usuario",
            entity_id=user.id,
            metadata={"role": user.role},
        )
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail ou funcionário já está vinculado a outro usuário.",
        ) from None
    return _user_read(user)


@router.patch("/{user_id}", response_model=UsuarioRead)
def update_user(
    user_id: int,
    payload: UsuarioUpdate,
    db: Session = Depends(get_db_session),
    actor: Usuario | None = Depends(require_permission("users:manage")),
) -> UsuarioRead:
    user = db.get(Usuario, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    _ensure_employee(db, payload.funcionario_id)
    updates = payload.model_dump(exclude_unset=True)
    role_changed = "role" in updates and updates["role"] != user.role
    if "senha" in updates:
        user.senha_hash = hash_password(updates.pop("senha"))
    if "funcionario_id" in updates and updates["funcionario_id"] is None:
        user.funcionario_id = None
        updates.pop("funcionario_id")
    if "email" in updates and updates["email"] is not None:
        user.email = updates.pop("email")
    for field_name, value in updates.items():
        setattr(user, field_name, value)
    try:
        db.flush()
        add_audit_log(
            db,
            user_id=actor.id if actor else None,
            action="role_changed" if role_changed else "user_updated",
            entity="usuario",
            entity_id=user.id,
            metadata={"role": user.role} if role_changed else None,
        )
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail ou funcionário já está vinculado a outro usuário.",
        ) from None
    return _user_read(user)
