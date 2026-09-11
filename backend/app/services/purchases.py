"""Fluxo de pedidos de compra e recebimentos confirmados."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Fornecedor,
    HistoricoCustoProduto,
    PedidoCompra,
    PedidoCompraItem,
    Produto,
    RecebimentoCompra,
    RecebimentoCompraItem,
)
from app.schemas.inventory import StockMovementCreate
from app.schemas.purchases import PurchaseCreate, PurchaseUpdate, ReceiptCreate
from app.services.inventory import (
    InventoryNotFound,
    create_movement,
    get_default_deposit,
)


class PurchaseNotFound(Exception):
    pass


class PurchaseConflict(Exception):
    pass


class PurchaseValidationError(Exception):
    pass


def purchase_query():
    return select(PedidoCompra).options(selectinload(PedidoCompra.itens))


def receipt_query():
    return select(RecebimentoCompra).options(
        selectinload(RecebimentoCompra.itens)
    )


def get_purchase(db: Session, purchase_id: int) -> PedidoCompra | None:
    return db.scalar(purchase_query().where(PedidoCompra.id == purchase_id))


def get_receipt(db: Session, receipt_id: int) -> RecebimentoCompra | None:
    return db.scalar(receipt_query().where(RecebimentoCompra.id == receipt_id))


def create_purchase(db: Session, payload: PurchaseCreate) -> PedidoCompra:
    supplier = db.get(Fornecedor, payload.fornecedor_id)
    if supplier is None:
        raise PurchaseNotFound("Fornecedor não encontrado.")
    product_ids = [item.produto_id for item in payload.itens]
    if len(product_ids) != len(set(product_ids)):
        raise PurchaseValidationError("O mesmo produto não pode aparecer duas vezes.")
    products = {
        product.id: product
        for product in db.scalars(
            select(Produto).where(Produto.id.in_(product_ids))
        ).all()
    }
    items = []
    for item in payload.itens:
        product = products.get(item.produto_id)
        if product is None:
            raise PurchaseNotFound("Produto não encontrado.")
        items.append(
            PedidoCompraItem(
                produto_id=product.id,
                produto_nome=product.nome,
                sku=product.sku,
                quantidade=item.quantidade,
                custo_unitario=item.custo_unitario,
            )
        )
    purchase = PedidoCompra(
        numero=payload.numero or f"PC-{uuid4().hex[:12].upper()}",
        fornecedor_id=supplier.id,
        previsao_entrega=payload.previsao_entrega,
        observacao=payload.observacao,
        itens=items,
    )
    db.add(purchase)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise PurchaseConflict("Número de pedido de compra já cadastrado.") from None
    return get_purchase(db, purchase.id)  # type: ignore[return-value]


def update_purchase(
    db: Session, purchase_id: int, payload: PurchaseUpdate
) -> PedidoCompra:
    purchase = get_purchase(db, purchase_id)
    if purchase is None:
        raise PurchaseNotFound("Pedido de compra não encontrado.")
    if purchase.status != "RASCUNHO" or any(
        item.quantidade_recebida > 0 for item in purchase.itens
    ):
        raise PurchaseConflict(
            "Somente pedido em rascunho e sem recebimentos pode ser editado."
        )
    data = payload.model_dump(exclude_unset=True)
    if payload.fornecedor_id is not None:
        supplier = db.get(Fornecedor, payload.fornecedor_id)
        if supplier is None:
            raise PurchaseNotFound("Fornecedor não encontrado.")
    if payload.itens is not None:
        product_ids = [item.produto_id for item in payload.itens]
        if len(product_ids) != len(set(product_ids)):
            raise PurchaseValidationError(
                "O mesmo produto não pode aparecer duas vezes."
            )
        products = {
            product.id: product
            for product in db.scalars(
                select(Produto).where(Produto.id.in_(product_ids))
            ).all()
        }
        purchase.itens.clear()
        for item in payload.itens:
            product = products.get(item.produto_id)
            if product is None:
                raise PurchaseNotFound("Produto não encontrado.")
            purchase.itens.append(
                PedidoCompraItem(
                    produto_id=product.id,
                    produto_nome=product.nome,
                    sku=product.sku,
                    quantidade=item.quantidade,
                    custo_unitario=item.custo_unitario,
                )
            )
        data.pop("itens", None)
    for field, value in data.items():
        setattr(purchase, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise PurchaseConflict("Número de pedido de compra já cadastrado.") from None
    return get_purchase(db, purchase.id)  # type: ignore[return-value]


def change_purchase_status(db: Session, purchase_id: int, status: str) -> PedidoCompra:
    purchase = get_purchase(db, purchase_id)
    if purchase is None:
        raise PurchaseNotFound("Pedido de compra não encontrado.")
    transitions = {
        "RASCUNHO": {"EMITIDO", "CANCELADO"},
        "EMITIDO": {"CANCELADO"},
        "PARCIALMENTE_RECEBIDO": {"CANCELADO"},
        "RECEBIDO": set(),
        "CANCELADO": set(),
    }
    if status != purchase.status and status not in transitions[purchase.status]:
        raise PurchaseConflict(
            f"Transição de compra {purchase.status} para {status} não permitida."
        )
    if status == "CANCELADO" and any(
        item.quantidade_recebida > 0 for item in purchase.itens
    ):
        raise PurchaseConflict("Pedido com recebimento não pode ser cancelado.")
    purchase.status = status
    db.commit()
    return get_purchase(db, purchase.id)  # type: ignore[return-value]


def create_receipt(
    db: Session,
    purchase_id: int,
    payload: ReceiptCreate,
    *,
    user_id: int | None = None,
) -> RecebimentoCompra:
    purchase = get_purchase(db, purchase_id)
    if purchase is None:
        raise PurchaseNotFound("Pedido de compra não encontrado.")
    if purchase.status in {"RASCUNHO", "CANCELADO", "RECEBIDO"}:
        raise PurchaseConflict("Pedido não está disponível para recebimento.")
    item_map = {item.id: item for item in purchase.itens}
    if len({item.pedido_item_id for item in payload.itens}) != len(payload.itens):
        raise PurchaseValidationError("O mesmo item não pode aparecer duas vezes.")
    receipt_items = []
    for payload_item in payload.itens:
        purchase_item = item_map.get(payload_item.pedido_item_id)
        if purchase_item is None:
            raise PurchaseNotFound("Item do pedido de compra não encontrado.")
        pending = purchase_item.quantidade - purchase_item.quantidade_recebida
        if payload_item.quantidade > pending:
            raise PurchaseValidationError(
                "Quantidade recebida maior que a quantidade pendente."
            )
        receipt_items.append(
            RecebimentoCompraItem(
                pedido_item_id=purchase_item.id,
                produto_id=purchase_item.produto_id,
                quantidade=payload_item.quantidade,
                custo_efetivo=payload_item.custo_efetivo,
            )
        )
    receipt = RecebimentoCompra(
        pedido_id=purchase.id,
        data_recebimento=payload.data_recebimento,
        usuario_id=user_id,
        observacao=payload.observacao,
        itens=receipt_items,
    )
    db.add(receipt)
    db.commit()
    from app.services.finance import ensure_receipt_payable

    ensure_receipt_payable(db, receipt.id)
    return get_receipt(db, receipt.id)  # type: ignore[return-value]


def confirm_receipt(
    db: Session, receipt_id: int, *, user_id: int | None = None
) -> RecebimentoCompra:
    receipt = get_receipt(db, receipt_id)
    if receipt is None:
        raise PurchaseNotFound("Recebimento não encontrado.")
    if receipt.status == "CONFIRMADO":
        return receipt
    if receipt.status != "RASCUNHO":
        raise PurchaseConflict("Somente recebimento em rascunho pode ser confirmado.")
    purchase = get_purchase(db, receipt.pedido_id)
    if purchase is None:
        raise PurchaseNotFound("Pedido de compra não encontrado.")
    try:
        default_deposit = get_default_deposit(db)
    except InventoryNotFound as exception:
        raise PurchaseConflict(str(exception)) from None
    try:
        for item in receipt.itens:
            purchase_item = db.get(PedidoCompraItem, item.pedido_item_id)
            if purchase_item is None:
                raise PurchaseNotFound("Item do pedido de compra não encontrado.")
            movement = StockMovementCreate(
                produto_id=item.produto_id,
                deposito_id=default_deposit.id,
                tipo="ENTRADA",
                quantidade=item.quantidade,
                data_movimentacao=datetime.combine(
                    receipt.data_recebimento,
                    datetime.min.time(),
                    tzinfo=timezone.utc,
                ),
                origem="RECEBIMENTO_COMPRA",
                documento_tipo="RECEBIMENTO_COMPRA",
                documento_id=receipt.id,
                chave_idempotencia=f"RECEBIMENTO-{receipt.id}-{item.id}",
            )
            create_movement(db, movement, user_id=user_id, commit=False)
            purchase_item.quantidade_recebida += item.quantidade
            db.add(
                HistoricoCustoProduto(
                    produto_id=item.produto_id,
                    fornecedor_id=purchase.fornecedor_id,
                    custo=item.custo_efetivo,
                    origem="recebimento_compra",
                )
            )
        receipt.status = "CONFIRMADO"
        purchase.status = (
            "RECEBIDO"
            if all(
                item.quantidade_recebida >= item.quantidade
                for item in purchase.itens
            )
            else "PARCIALMENTE_RECEBIDO"
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return get_receipt(db, receipt.id)  # type: ignore[return-value]


def purchase_to_read(purchase: PedidoCompra):
    from app.schemas.purchases import PurchaseItemRead, PurchaseRead

    return PurchaseRead(
        id=purchase.id,
        numero=purchase.numero,
        fornecedor_id=purchase.fornecedor_id,
        status=purchase.status,
        previsao_entrega=purchase.previsao_entrega,
        observacao=purchase.observacao,
        created_at=purchase.created_at,
        updated_at=purchase.updated_at,
        itens=[
            PurchaseItemRead(
                id=item.id,
                produto_id=item.produto_id,
                produto_nome=item.produto_nome,
                sku=item.sku,
                quantidade=item.quantidade,
                quantidade_recebida=item.quantidade_recebida,
                pendente=item.quantidade - item.quantidade_recebida,
                custo_unitario=item.custo_unitario,
            )
            for item in purchase.itens
        ],
    )


def receipt_to_read(receipt: RecebimentoCompra):
    from app.schemas.purchases import ReceiptItemRead, ReceiptRead

    return ReceiptRead(
        id=receipt.id,
        pedido_id=receipt.pedido_id,
        data_recebimento=receipt.data_recebimento,
        status=receipt.status,
        usuario_id=receipt.usuario_id,
        observacao=receipt.observacao,
        created_at=receipt.created_at,
        updated_at=receipt.updated_at,
        itens=[ReceiptItemRead.model_validate(item) for item in receipt.itens],
    )
