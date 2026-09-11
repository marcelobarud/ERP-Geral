from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import require_authenticated, require_permission
from app.db.session import get_db_session
from app.models import Cliente, Produto, Venda, VendaItem
from app.schemas.customers import (
    ClienteCreate,
    ClienteDetailRead,
    ClienteProdutoCompradoRead,
    ClienteRead,
    ClienteUpdate,
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
    prefix="/api/customers",
    tags=["customers"],
    dependencies=[Depends(require_authenticated)],
)


@router.get("", response_model=PaginationResponse[ClienteRead])
def list_customers(
    search: str | None = Query(default=None),
    city: str | None = Query(default=None),
    state: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db_session),
) -> PaginationResponse[ClienteRead]:
    query = select(Cliente)
    normalized_search = search.strip() if search else ""
    normalized_city = city.strip() if city else ""
    normalized_state = state.strip() if state else ""
    if normalized_search:
        pattern = f"%{normalized_search}%"
        query = query.where(
            or_(
                Cliente.nome.ilike(pattern),
                Cliente.cidade.ilike(pattern),
                Cliente.estado.ilike(pattern),
            )
        )
    if normalized_city:
        query = query.where(Cliente.cidade.ilike(normalized_city))
    if normalized_state:
        query = query.where(Cliente.estado.ilike(normalized_state))
    items, total, total_pages = paginate(
        db, query.order_by(Cliente.id), page, page_size
    )
    return PaginationResponse[ClienteRead](
        items=list(items),
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.get("/{customer_id}", response_model=ClienteDetailRead)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db_session),
) -> ClienteDetailRead:
    customer = db.get(Cliente, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    purchased_products_query = (
        select(
            Produto.id.label("produto_id"),
            Produto.nome,
            func.sum(VendaItem.quantidade).label("quantidade"),
        )
        .join(VendaItem, VendaItem.produto_id == Produto.id)
        .join(Venda, Venda.id == VendaItem.venda_id)
        .where(Venda.cliente_id == customer_id)
        .group_by(Produto.id, Produto.nome)
        .order_by(Produto.id)
    )
    purchased_products = [
        ClienteProdutoCompradoRead(
            produto_id=row.produto_id,
            nome=row.nome,
            quantidade=row.quantidade,
        )
        for row in db.execute(purchased_products_query)
    ]
    customer_read = ClienteRead(
        **ClienteRead.model_validate(customer).model_dump(
            exclude={"campos_personalizados"}
        ),
        campos_personalizados=read_values(
            db, CUSTOM_FIELD_DOMAINS["customers"], customer.id
        ),
    )
    return ClienteDetailRead(
        **customer_read.model_dump(),
        produtos_comprados=purchased_products,
    )


@router.post(
    "",
    response_model=ClienteRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("customers:write"))],
)
def create_customer(
    payload: ClienteCreate,
    db: Session = Depends(get_db_session),
) -> Cliente:
    custom_values = payload.campos_personalizados
    customer = Cliente(**payload.model_dump(exclude={"campos_personalizados"}))
    db.add(customer)
    try:
        db.flush()
        apply_values(db, CUSTOM_FIELD_DOMAINS["customers"], customer.id, custom_values)
        db.commit()
        db.refresh(customer)
    except CustomFieldValidationError as exception:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exception)) from None
    return ClienteRead(
        **ClienteRead.model_validate(customer).model_dump(
            exclude={"campos_personalizados"}
        ),
        campos_personalizados=read_values(
            db, CUSTOM_FIELD_DOMAINS["customers"], customer.id
        ),
    )


@router.patch(
    "/{customer_id}",
    response_model=ClienteRead,
    dependencies=[Depends(require_permission("customers:write"))],
)
def update_customer(
    customer_id: int,
    payload: ClienteUpdate,
    db: Session = Depends(get_db_session),
) -> Cliente:
    customer = db.get(Cliente, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    updates = payload.model_dump(exclude_unset=True)
    custom_values = updates.pop("campos_personalizados", None)
    for field_name, value in updates.items():
        setattr(customer, field_name, value)
    try:
        db.flush()
        apply_values(
            db,
            CUSTOM_FIELD_DOMAINS["customers"],
            customer.id,
            custom_values or {},
        )
        db.commit()
        db.refresh(customer)
    except CustomFieldValidationError as exception:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exception)) from None
    return ClienteRead(
        **ClienteRead.model_validate(customer).model_dump(
            exclude={"campos_personalizados"}
        ),
        campos_personalizados=read_values(
            db, CUSTOM_FIELD_DOMAINS["customers"], customer.id
        ),
    )


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("customers:write"))],
)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db_session),
) -> Response:
    customer = db.get(Cliente, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    if db.scalar(select(Venda.id).where(Venda.cliente_id == customer_id)) is not None:
        raise HTTPException(
            status_code=409,
            detail="Cliente possui vendas relacionadas e não pode ser excluído.",
        )
    db.delete(customer)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Cliente possui vendas relacionadas e não pode ser excluído.",
        ) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
