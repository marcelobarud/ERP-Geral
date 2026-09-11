from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import require_authenticated, require_permission
from app.db.session import get_db_session
from app.models import Funcionario, Venda
from app.schemas.employees import (
    FuncionarioCreate,
    FuncionarioRead,
    FuncionarioUpdate,
)
from app.schemas.pagination import PaginationResponse
from app.services.custom_fields import (
    CUSTOM_FIELD_DOMAINS,
    CustomFieldValidationError,
    apply_values,
    read_values,
)
from app.services.pagination import paginate

router = APIRouter(
    prefix="/api/employees",
    tags=["employees"],
    dependencies=[Depends(require_authenticated)],
)


def ensure_unique_cpf(
    db: Session,
    cpf: str,
    employee_id: int | None = None,
) -> None:
    query = select(Funcionario).where(Funcionario.cpf == cpf)
    if employee_id is not None:
        query = query.where(Funcionario.id != employee_id)
    if db.scalar(query) is not None:
        raise HTTPException(status_code=409, detail="CPF já cadastrado.")


@router.get("", response_model=PaginationResponse[FuncionarioRead])
def list_employees(
    active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    city: str | None = Query(default=None),
    state: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db_session),
) -> PaginationResponse[FuncionarioRead]:
    query = select(Funcionario)
    if active is not None:
        query = query.where(Funcionario.ativo == active)
    normalized_search = search.strip() if search else ""
    normalized_city = city.strip() if city else ""
    normalized_state = state.strip() if state else ""
    if normalized_search:
        search_pattern = f"%{normalized_search}%"
        query = query.where(
            or_(
                Funcionario.nome_completo.ilike(search_pattern),
                Funcionario.cpf.ilike(search_pattern),
                Funcionario.cidade.ilike(search_pattern),
                Funcionario.estado.ilike(search_pattern),
            )
        )
    if normalized_city:
        query = query.where(Funcionario.cidade.ilike(normalized_city))
    if normalized_state:
        query = query.where(Funcionario.estado.ilike(normalized_state))
    items, total, total_pages = paginate(
        db, query.order_by(Funcionario.id), page, page_size
    )
    return PaginationResponse[FuncionarioRead](
        items=list(items),
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.get("/{employee_id}", response_model=FuncionarioRead)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db_session),
) -> Funcionario:
    employee = db.get(Funcionario, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado.")
    return FuncionarioRead(
        **FuncionarioRead.model_validate(employee).model_dump(
            exclude={"campos_personalizados"}
        ),
        campos_personalizados=read_values(
            db, CUSTOM_FIELD_DOMAINS["employees"], employee.id
        ),
    )


@router.post(
    "",
    response_model=FuncionarioRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("employees:write"))],
)
def create_employee(
    payload: FuncionarioCreate,
    db: Session = Depends(get_db_session),
) -> Funcionario:
    ensure_unique_cpf(db, payload.cpf)
    custom_values = payload.campos_personalizados
    employee = Funcionario(**payload.model_dump(exclude={"campos_personalizados"}))
    db.add(employee)
    try:
        db.flush()
        apply_values(db, CUSTOM_FIELD_DOMAINS["employees"], employee.id, custom_values)
        db.commit()
    except CustomFieldValidationError as exception:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exception)) from None
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="CPF já cadastrado.") from None
    db.refresh(employee)
    return FuncionarioRead(
        **FuncionarioRead.model_validate(employee).model_dump(
            exclude={"campos_personalizados"}
        ),
        campos_personalizados=read_values(
            db, CUSTOM_FIELD_DOMAINS["employees"], employee.id
        ),
    )


@router.patch(
    "/{employee_id}",
    response_model=FuncionarioRead,
    dependencies=[Depends(require_permission("employees:write"))],
)
def update_employee(
    employee_id: int,
    payload: FuncionarioUpdate,
    db: Session = Depends(get_db_session),
) -> Funcionario:
    employee = db.get(Funcionario, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado.")

    updates = payload.model_dump(exclude_unset=True)
    custom_values = updates.pop("campos_personalizados", None)
    if "cpf" in updates:
        ensure_unique_cpf(db, updates["cpf"], employee_id)
    for field_name, value in updates.items():
        setattr(employee, field_name, value)
    try:
        db.flush()
        apply_values(
            db,
            CUSTOM_FIELD_DOMAINS["employees"],
            employee.id,
            custom_values or {},
        )
        db.commit()
    except CustomFieldValidationError as exception:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exception)) from None
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="CPF já cadastrado.") from None
    db.refresh(employee)
    return FuncionarioRead(
        **FuncionarioRead.model_validate(employee).model_dump(
            exclude={"campos_personalizados"}
        ),
        campos_personalizados=read_values(
            db, CUSTOM_FIELD_DOMAINS["employees"], employee.id
        ),
    )


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("employees:write"))],
)
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db_session),
) -> Response:
    employee = db.get(Funcionario, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado.")
    if (
        db.scalar(
            select(Venda.id).where(
                Venda.funcionario_id == employee_id,
                Venda.status != "CANCELADA",
            )
        )
        is not None
    ):
        raise HTTPException(
            status_code=409,
            detail="Funcionário possui vendas relacionadas e não pode ser excluído.",
        )
    # Keep cancelled sales and their historical employee reference intact.
    # Once no active sale depends on the employee, deletion is represented by
    # deactivation because the employee foreign key is intentionally required.
    employee.ativo = False
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Funcionário não pode ser excluído.",
        ) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
