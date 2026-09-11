from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import require_authenticated, require_permission
from app.db.session import get_db_session
from app.models import Cliente, CondicaoPagamento, Orcamento, PedidoVenda
from app.schemas.commercial import (
    OrderCreate,
    OrderRead,
    OrderStatusUpdate,
    OrderUpdate,
    PaymentConditionCreate,
    PaymentConditionRead,
    PaymentConditionUpdate,
    QuoteCreate,
    QuoteRead,
    QuoteStatusUpdate,
    QuoteUpdate,
)
from app.services.commercial import (
    CommercialConflict,
    CommercialNotFound,
    CommercialValidationError,
    change_order_status,
    change_quote_status,
    convert_order_to_sale,
    convert_quote_to_order,
    create_order,
    create_quote,
    document_html,
    get_order,
    get_quote,
    order_query,
    order_to_read,
    quote_query,
    quote_to_read,
    update_order,
    update_quote,
)

router = APIRouter(
    prefix="/api/commercial",
    tags=["commercial"],
    dependencies=[Depends(require_authenticated)],
)


@router.get("/payment-conditions", response_model=list[PaymentConditionRead])
def list_payment_conditions(
    include_inactive: bool = Query(default=False),
    db: Session = Depends(get_db_session),
) -> list[PaymentConditionRead]:
    query = select(CondicaoPagamento).order_by(CondicaoPagamento.nome)
    if not include_inactive:
        query = query.where(CondicaoPagamento.ativo.is_(True))
    conditions = db.scalars(query).all()
    return [PaymentConditionRead.model_validate(condition) for condition in conditions]


@router.post(
    "/payment-conditions",
    response_model=PaymentConditionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("commercial:write"))],
)
def create_payment_condition(
    payload: PaymentConditionCreate,
    db: Session = Depends(get_db_session),
) -> PaymentConditionRead:
    condition = CondicaoPagamento(**payload.model_dump())
    db.add(condition)
    try:
        db.commit()
        db.refresh(condition)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Código já cadastrado.") from None
    return PaymentConditionRead.model_validate(condition)


@router.patch(
    "/payment-conditions/{condition_id}",
    response_model=PaymentConditionRead,
    dependencies=[Depends(require_permission("commercial:write"))],
)
def update_payment_condition(
    condition_id: int,
    payload: PaymentConditionUpdate,
    db: Session = Depends(get_db_session),
) -> PaymentConditionRead:
    condition = db.get(CondicaoPagamento, condition_id)
    if condition is None:
        raise HTTPException(
            status_code=404, detail="Condição de pagamento não encontrada."
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(condition, field, value)
    try:
        db.commit()
        db.refresh(condition)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Código já cadastrado.") from None
    return PaymentConditionRead.model_validate(condition)


@router.get("/quotes", response_model=list[QuoteRead])
def list_quotes(
    search: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db_session),
) -> list[QuoteRead]:
    query = quote_query().join(Orcamento.cliente).order_by(
        Orcamento.created_at.desc(), Orcamento.id.desc()
    )
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        query = query.where(
            (Orcamento.numero.ilike(pattern)) | (Cliente.nome.ilike(pattern))
        )
    if status_filter:
        query = query.where(Orcamento.status == status_filter)
    return [quote_to_read(quote) for quote in db.scalars(query).all()]


@router.post(
    "/quotes",
    response_model=QuoteRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("commercial:write"))],
)
def create_quote_endpoint(
    payload: QuoteCreate,
    db: Session = Depends(get_db_session),
) -> QuoteRead:
    try:
        return quote_to_read(create_quote(db, payload))
    except CommercialNotFound as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from None
    except CommercialValidationError as exception:
        raise HTTPException(status_code=422, detail=str(exception)) from None
    except CommercialConflict as exception:
        raise HTTPException(status_code=409, detail=str(exception)) from None


@router.get("/quotes/{quote_id}", response_model=QuoteRead)
def get_quote_endpoint(
    quote_id: int, db: Session = Depends(get_db_session)
) -> QuoteRead:
    quote = get_quote(db, quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado.")
    return quote_to_read(quote)


@router.patch(
    "/quotes/{quote_id}",
    response_model=QuoteRead,
    dependencies=[Depends(require_permission("commercial:write"))],
)
def update_quote_endpoint(
    quote_id: int,
    payload: QuoteUpdate,
    db: Session = Depends(get_db_session),
) -> QuoteRead:
    try:
        return quote_to_read(update_quote(db, quote_id, payload))
    except CommercialNotFound as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from None
    except CommercialValidationError as exception:
        raise HTTPException(status_code=422, detail=str(exception)) from None
    except CommercialConflict as exception:
        raise HTTPException(status_code=409, detail=str(exception)) from None


@router.patch(
    "/quotes/{quote_id}/status",
    response_model=QuoteRead,
    dependencies=[Depends(require_permission("commercial:write"))],
)
def change_quote_status_endpoint(
    quote_id: int,
    payload: QuoteStatusUpdate,
    db: Session = Depends(get_db_session),
) -> QuoteRead:
    try:
        return quote_to_read(change_quote_status(db, quote_id, payload.status))
    except CommercialNotFound as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from None
    except CommercialConflict as exception:
        raise HTTPException(status_code=409, detail=str(exception)) from None


@router.post(
    "/quotes/{quote_id}/convert-to-order",
    response_model=OrderRead,
    dependencies=[Depends(require_permission("commercial:write"))],
)
def convert_quote_endpoint(
    quote_id: int, db: Session = Depends(get_db_session)
) -> OrderRead:
    try:
        return order_to_read(convert_quote_to_order(db, quote_id))
    except CommercialNotFound as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from None
    except CommercialConflict as exception:
        raise HTTPException(status_code=409, detail=str(exception)) from None


@router.get("/quotes/{quote_id}/print", response_class=HTMLResponse)
def print_quote(quote_id: int, db: Session = Depends(get_db_session)) -> HTMLResponse:
    quote = get_quote(db, quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado.")
    return HTMLResponse(document_html("Orçamento", quote, quote.itens))


@router.get("/orders", response_model=list[OrderRead])
def list_orders(
    search: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db_session),
) -> list[OrderRead]:
    query = order_query().join(PedidoVenda.cliente).order_by(
        PedidoVenda.created_at.desc(), PedidoVenda.id.desc()
    )
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        query = query.where(
            (PedidoVenda.numero.ilike(pattern)) | (Cliente.nome.ilike(pattern))
        )
    if status_filter:
        query = query.where(PedidoVenda.status == status_filter)
    return [order_to_read(order) for order in db.scalars(query).all()]


@router.post(
    "/orders",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("commercial:write"))],
)
def create_order_endpoint(
    payload: OrderCreate,
    db: Session = Depends(get_db_session),
) -> OrderRead:
    try:
        return order_to_read(create_order(db, payload))
    except CommercialNotFound as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from None
    except CommercialValidationError as exception:
        raise HTTPException(status_code=422, detail=str(exception)) from None
    except CommercialConflict as exception:
        raise HTTPException(status_code=409, detail=str(exception)) from None


@router.get("/orders/{order_id}", response_model=OrderRead)
def get_order_endpoint(
    order_id: int, db: Session = Depends(get_db_session)
) -> OrderRead:
    order = get_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    return order_to_read(order)


@router.patch(
    "/orders/{order_id}",
    response_model=OrderRead,
    dependencies=[Depends(require_permission("commercial:write"))],
)
def update_order_endpoint(
    order_id: int,
    payload: OrderUpdate,
    db: Session = Depends(get_db_session),
) -> OrderRead:
    try:
        return order_to_read(update_order(db, order_id, payload))
    except CommercialNotFound as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from None
    except CommercialValidationError as exception:
        raise HTTPException(status_code=422, detail=str(exception)) from None
    except CommercialConflict as exception:
        raise HTTPException(status_code=409, detail=str(exception)) from None


@router.patch(
    "/orders/{order_id}/status",
    response_model=OrderRead,
    dependencies=[Depends(require_permission("commercial:write"))],
)
def change_order_status_endpoint(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db_session),
) -> OrderRead:
    try:
        return order_to_read(change_order_status(db, order_id, payload.status))
    except CommercialNotFound as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from None
    except CommercialConflict as exception:
        raise HTTPException(status_code=409, detail=str(exception)) from None


@router.post(
    "/orders/{order_id}/convert-to-sale",
    response_model=dict,
    dependencies=[Depends(require_permission("sales:create"))],
)
def convert_order_endpoint(
    order_id: int,
    db: Session = Depends(get_db_session),
) -> dict:
    try:
        sale = convert_order_to_sale(db, order_id)
        return sale.model_dump(mode="json")
    except CommercialNotFound as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from None
    except CommercialConflict as exception:
        raise HTTPException(status_code=409, detail=str(exception)) from None


@router.get("/orders/{order_id}/print", response_class=HTMLResponse)
def print_order(order_id: int, db: Session = Depends(get_db_session)) -> HTMLResponse:
    order = get_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    return HTMLResponse(document_html("Pedido de venda", order, order.itens))
