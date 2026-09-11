from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.dependencies import require_authenticated, require_permission
from app.db.session import get_db_session
from app.models import Cliente, Funcionario, Produto, Usuario, Venda, VendaItem
from app.schemas.pagination import PaginationResponse
from app.schemas.sales import VendaCancel, VendaCreate, VendaRead, VendaStatus
from app.services.pagination import paginate
from app.services.sales import (
    SaleEmployeeInactive,
    SaleNotFound,
    SalePersistenceError,
    SaleProductInactive,
    SaleReferenceNotFound,
    cancel_sale,
    create_sale,
    get_sale,
    sale_query,
    sale_to_read,
)

router = APIRouter(
    prefix="/api/sales",
    tags=["sales"],
    dependencies=[Depends(require_authenticated)],
)


@router.post(
    "",
    response_model=VendaRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("sales:create"))],
)
def create_sale_endpoint(
    payload: VendaCreate,
    db: Session = Depends(get_db_session),
) -> VendaRead:
    try:
        sale = create_sale(db, payload)
    except SaleReferenceNotFound as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from None
    except SaleEmployeeInactive as exception:
        raise HTTPException(status_code=422, detail=str(exception)) from None
    except SaleProductInactive as exception:
        raise HTTPException(status_code=422, detail=str(exception)) from None
    except SalePersistenceError:
        raise HTTPException(
            status_code=409,
            detail="Não foi possível persistir a venda por conflito de integridade.",
        ) from None
    return sale_to_read(sale)


@router.get("", response_model=PaginationResponse[VendaRead])
def list_sales(
    search: str | None = Query(default=None),
    product_id: int | None = Query(default=None, gt=0),
    customer_id: int | None = Query(default=None, gt=0),
    employee_id: int | None = Query(default=None, gt=0),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    total_min: Decimal | None = Query(default=None, ge=0),
    total_max: Decimal | None = Query(default=None, ge=0),
    status_filter: VendaStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db_session),
) -> PaginationResponse[VendaRead]:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(
            status_code=422,
            detail="A data inicial não pode ser posterior à data final.",
        )
    if total_min is not None and total_max is not None and total_min > total_max:
        raise HTTPException(
            status_code=422,
            detail="O total mínimo não pode ser maior que o máximo.",
        )

    query = sale_query()
    normalized_search = search.strip() if search else ""
    if normalized_search:
        pattern = f"%{normalized_search}%"
        query = query.where(
            or_(
                Venda.cliente.has(Cliente.nome.ilike(pattern)),
                Venda.funcionario.has(Funcionario.nome_completo.ilike(pattern)),
                Venda.itens.any(
                    VendaItem.produto.has(Produto.nome.ilike(pattern))
                ),
            )
        )
    if product_id is not None:
        query = query.where(Venda.itens.any(VendaItem.produto_id == product_id))
    if customer_id is not None:
        query = query.where(Venda.cliente_id == customer_id)
    if employee_id is not None:
        query = query.where(Venda.funcionario_id == employee_id)
    if date_from is not None:
        query = query.where(
            Venda.data_venda
            >= datetime.combine(date_from, time.min, tzinfo=timezone.utc)
        )
    if date_to is not None:
        exclusive_end = date_to + timedelta(days=1)
        query = query.where(
            Venda.data_venda
            < datetime.combine(exclusive_end, time.min, tzinfo=timezone.utc)
        )
    sale_total = (
        select(
            func.coalesce(
                func.sum(VendaItem.quantidade * VendaItem.preco_unitario),
                Decimal("0.00"),
            )
        )
        .where(VendaItem.venda_id == Venda.id)
        .correlate(Venda)
        .scalar_subquery()
    )
    if total_min is not None:
        query = query.where(sale_total >= total_min)
    if total_max is not None:
        query = query.where(sale_total <= total_max)
    if status_filter is not None:
        query = query.where(Venda.status == status_filter)

    sales, total, total_pages = paginate(
        db,
        query.order_by(Venda.data_venda.desc(), Venda.id.desc()),
        page,
        page_size,
    )
    return PaginationResponse[VendaRead](
        items=[sale_to_read(sale) for sale in sales],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.get("/{sale_id}", response_model=VendaRead)
def get_sale_endpoint(
    sale_id: int,
    db: Session = Depends(get_db_session),
) -> VendaRead:
    sale = get_sale(db, sale_id)
    if sale is None:
        raise HTTPException(status_code=404, detail="Venda não encontrada.")
    return sale_to_read(sale)


@router.post(
    "/{sale_id}/cancel",
    response_model=VendaRead,
)
def cancel_sale_endpoint(
    sale_id: int,
    payload: VendaCancel,
    db: Session = Depends(get_db_session),
    actor: Usuario | None = Depends(require_permission("sales:cancel")),
) -> VendaRead:
    try:
        sale = cancel_sale(
            db,
            sale_id,
            payload,
            actor_user_id=actor.id if actor else None,
        )
    except SaleNotFound as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from None
    except SalePersistenceError:
        raise HTTPException(
            status_code=409,
            detail="Não foi possível cancelar a venda por conflito de integridade.",
        ) from None
    return sale_to_read(sale)
