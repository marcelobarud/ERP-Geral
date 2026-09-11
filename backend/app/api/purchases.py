from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.dependencies import require_authenticated, require_permission
from app.db.session import get_db_session
from app.models import Fornecedor, PedidoCompra, RecebimentoCompra, Usuario
from app.schemas.purchases import (
    PurchaseCreate,
    PurchaseRead,
    PurchaseStatusUpdate,
    PurchaseUpdate,
    ReceiptCreate,
    ReceiptRead,
)
from app.services.auth import add_audit_log
from app.services.purchases import (
    PurchaseConflict,
    PurchaseNotFound,
    PurchaseValidationError,
    change_purchase_status,
    confirm_receipt,
    create_purchase,
    create_receipt,
    get_purchase,
    get_receipt,
    purchase_query,
    purchase_to_read,
    receipt_query,
    receipt_to_read,
    update_purchase,
)

router = APIRouter(
    prefix="/api/purchases",
    tags=["purchases"],
    dependencies=[Depends(require_authenticated)],
)


@router.get("", response_model=list[PurchaseRead])
def list_purchases(
    search: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db_session),
) -> list[PurchaseRead]:
    query = purchase_query().join(PedidoCompra.fornecedor).order_by(
        PedidoCompra.created_at.desc()
    )
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(PedidoCompra.numero.ilike(pattern), Fornecedor.nome.ilike(pattern))
        )
    if status_filter:
        query = query.where(PedidoCompra.status == status_filter)
    return [purchase_to_read(item) for item in db.scalars(query).all()]


@router.patch(
    "/{purchase_id}",
    response_model=PurchaseRead,
    dependencies=[Depends(require_permission("purchases:write"))],
)
def update_purchase_endpoint(
    purchase_id: int,
    payload: PurchaseUpdate,
    db: Session = Depends(get_db_session),
    actor: Usuario | None = Depends(require_permission("purchases:write")),
) -> PurchaseRead:
    try:
        result = purchase_to_read(update_purchase(db, purchase_id, payload))
        add_audit_log(
            db,
            user_id=actor.id if actor else None,
            action="purchase_updated",
            entity="pedido_compra",
            entity_id=purchase_id,
        )
        db.commit()
        return result
    except PurchaseNotFound as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from None
    except PurchaseValidationError as exception:
        raise HTTPException(status_code=422, detail=str(exception)) from None
    except PurchaseConflict as exception:
        raise HTTPException(status_code=409, detail=str(exception)) from None


@router.post(
    "",
    response_model=PurchaseRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("purchases:write"))],
)
def create_purchase_endpoint(
    payload: PurchaseCreate,
    db: Session = Depends(get_db_session),
    actor: Usuario | None = Depends(require_permission("purchases:write")),
) -> PurchaseRead:
    try:
        purchase = create_purchase(db, payload)
        add_audit_log(
            db,
            user_id=actor.id if actor else None,
            action="purchase_created",
            entity="pedido_compra",
            entity_id=purchase.id,
        )
        db.commit()
        return purchase_to_read(purchase)
    except PurchaseNotFound as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from None
    except PurchaseValidationError as exception:
        raise HTTPException(status_code=422, detail=str(exception)) from None
    except PurchaseConflict as exception:
        raise HTTPException(status_code=409, detail=str(exception)) from None


@router.get("/{purchase_id}", response_model=PurchaseRead)
def get_purchase_endpoint(
    purchase_id: int, db: Session = Depends(get_db_session)
) -> PurchaseRead:
    purchase = get_purchase(db, purchase_id)
    if purchase is None:
        raise HTTPException(status_code=404, detail="Pedido de compra não encontrado.")
    return purchase_to_read(purchase)


@router.patch(
    "/{purchase_id}/status",
    response_model=PurchaseRead,
    dependencies=[Depends(require_permission("purchases:write"))],
)
def change_purchase_status_endpoint(
    purchase_id: int,
    payload: PurchaseStatusUpdate,
    db: Session = Depends(get_db_session),
    actor: Usuario | None = Depends(require_permission("purchases:write")),
) -> PurchaseRead:
    try:
        purchase = change_purchase_status(db, purchase_id, payload.status)
        add_audit_log(
            db,
            user_id=actor.id if actor else None,
            action="purchase_status_changed",
            entity="pedido_compra",
            entity_id=purchase_id,
            metadata={"status": payload.status},
        )
        db.commit()
        return purchase_to_read(purchase)
    except PurchaseNotFound as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from None
    except PurchaseConflict as exception:
        raise HTTPException(status_code=409, detail=str(exception)) from None


@router.get("/{purchase_id}/receipts", response_model=list[ReceiptRead])
def list_receipts(
    purchase_id: int, db: Session = Depends(get_db_session)
) -> list[ReceiptRead]:
    if get_purchase(db, purchase_id) is None:
        raise HTTPException(status_code=404, detail="Pedido de compra não encontrado.")
    receipts = db.scalars(
        receipt_query()
        .where(RecebimentoCompra.pedido_id == purchase_id)
        .order_by(RecebimentoCompra.created_at.desc())
    ).all()
    return [receipt_to_read(receipt) for receipt in receipts]


@router.post(
    "/{purchase_id}/receipts",
    response_model=ReceiptRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("purchases:write"))],
)
def create_receipt_endpoint(
    purchase_id: int,
    payload: ReceiptCreate,
    db: Session = Depends(get_db_session),
    actor: Usuario | None = Depends(require_permission("purchases:write")),
) -> ReceiptRead:
    try:
        receipt = create_receipt(
            db, purchase_id, payload, user_id=actor.id if actor else None
        )
        add_audit_log(
            db,
            user_id=actor.id if actor else None,
            action="receipt_created",
            entity="recebimento_compra",
            entity_id=receipt.id,
        )
        db.commit()
        return receipt_to_read(receipt)
    except PurchaseNotFound as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from None
    except PurchaseValidationError as exception:
        raise HTTPException(status_code=422, detail=str(exception)) from None
    except PurchaseConflict as exception:
        raise HTTPException(status_code=409, detail=str(exception)) from None


@router.post(
    "/receipts/{receipt_id}/confirm",
    response_model=ReceiptRead,
    dependencies=[Depends(require_permission("purchases:write"))],
)
def confirm_receipt_endpoint(
    receipt_id: int,
    db: Session = Depends(get_db_session),
    actor: Usuario | None = Depends(require_permission("purchases:write")),
) -> ReceiptRead:
    try:
        receipt = confirm_receipt(
            db, receipt_id, user_id=actor.id if actor else None
        )
        add_audit_log(
            db,
            user_id=actor.id if actor else None,
            action="receipt_confirmed",
            entity="recebimento_compra",
            entity_id=receipt_id,
        )
        db.commit()
        return receipt_to_read(receipt)
    except PurchaseNotFound as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from None
    except PurchaseConflict as exception:
        raise HTTPException(status_code=409, detail=str(exception)) from None


@router.get("/receipts/{receipt_id}", response_model=ReceiptRead)
def get_receipt_endpoint(
    receipt_id: int, db: Session = Depends(get_db_session)
) -> ReceiptRead:
    receipt = get_receipt(db, receipt_id)
    if receipt is None:
        raise HTTPException(status_code=404, detail="Recebimento não encontrado.")
    return receipt_to_read(receipt)
