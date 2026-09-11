"""Integração transacional entre vendas, estoque e devoluções."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    DevolucaoVenda,
    DevolucaoVendaItem,
    MovimentacaoEstoque,
    VendaItem,
)
from app.schemas.inventory import StockMovementCreate
from app.schemas.returns import ReturnCreate
from app.services.inventory import (
    InventoryConflict,
    InventoryNotFound,
    create_movement,
    get_default_deposit,
)
from app.services.sales import get_sale


class SalesStockConflict(Exception):
    pass


def post_sale_to_stock(db: Session, sale_id: int, user_id: int | None = None):
    sale = get_sale(db, sale_id)
    if sale is None:
        raise SalesStockConflict("Venda não encontrada.")
    existing = db.scalar(
        select(MovimentacaoEstoque.id).where(
            MovimentacaoEstoque.documento_tipo == "VENDA",
            MovimentacaoEstoque.documento_id == sale.id,
            MovimentacaoEstoque.tipo != "REVERSAO",
        )
    )
    if existing is not None:
        return sale
    if sale.status != "CONCLUIDA":
        raise SalesStockConflict("Somente venda concluída pode movimentar estoque.")
    try:
        default_deposit = get_default_deposit(db)
    except InventoryNotFound as exception:
        raise SalesStockConflict(str(exception)) from None
    try:
        for item in sale.itens:
            create_movement(
                db,
                StockMovementCreate(
                    produto_id=item.produto_id,
                    deposito_id=default_deposit.id,
                    tipo="SAIDA",
                    quantidade=item.quantidade,
                    data_movimentacao=sale.data_venda,
                    origem="VENDA",
                    documento_tipo="VENDA",
                    documento_id=sale.id,
                    chave_idempotencia=f"VENDA-{sale.id}-{item.id}",
                ),
                user_id=user_id,
                commit=False,
            )
        db.commit()
    except InventoryConflict as exception:
        db.rollback()
        raise SalesStockConflict(str(exception)) from None
    except Exception:
        db.rollback()
        raise
    return sale


def reverse_sale_stock(db: Session, sale_id: int, user_id: int | None = None) -> None:
    movements = db.scalars(
        select(MovimentacaoEstoque).where(
            MovimentacaoEstoque.documento_tipo == "VENDA",
            MovimentacaoEstoque.documento_id == sale_id,
            MovimentacaoEstoque.tipo != "REVERSAO",
        )
    ).all()
    try:
        for movement in movements:
            create_movement(
                db,
                StockMovementCreate(
                    produto_id=movement.produto_id,
                    deposito_id=movement.deposito_id,
                    tipo="REVERSAO",
                    quantidade=movement.quantidade,
                    data_movimentacao=datetime.now(timezone.utc),
                    origem="CANCELAMENTO_VENDA",
                    documento_tipo="VENDA_CANCELAMENTO",
                    documento_id=sale_id,
                    movimento_origem_id=movement.id,
                    chave_idempotencia=f"CANCELAMENTO-VENDA-{sale_id}-{movement.id}",
                ),
                user_id=user_id,
                commit=False,
            )
        db.flush()
    except InventoryConflict as exception:
        raise SalesStockConflict(str(exception)) from None


def return_query():
    return select(DevolucaoVenda).options(selectinload(DevolucaoVenda.itens))


def get_return(db: Session, return_id: int) -> DevolucaoVenda | None:
    return db.scalar(return_query().where(DevolucaoVenda.id == return_id))


def create_return(
    db: Session, sale_id: int, payload: ReturnCreate, user_id: int | None = None
) -> DevolucaoVenda:
    sale = get_sale(db, sale_id)
    if sale is None:
        raise SalesStockConflict("Venda não encontrada.")
    items_by_id = {item.id: item for item in sale.itens}
    if len({item.venda_item_id for item in payload.itens}) != len(payload.itens):
        raise SalesStockConflict("O mesmo item não pode aparecer duas vezes.")
    return_items = []
    for payload_item in payload.itens:
        sale_item = items_by_id.get(payload_item.venda_item_id)
        if sale_item is None:
            raise SalesStockConflict("Item da venda não encontrado.")
        return_items.append(
            DevolucaoVendaItem(
                venda_item_id=sale_item.id,
                produto_id=sale_item.produto_id,
                produto_nome=sale_item.produto.nome,
                quantidade=payload_item.quantidade,
                preco_unitario=sale_item.preco_unitario,
            )
        )
    record = DevolucaoVenda(
        venda_id=sale.id,
        motivo=payload.motivo,
        usuario_id=user_id,
        itens=return_items,
    )
    db.add(record)
    db.commit()
    return get_return(db, record.id)  # type: ignore[return-value]


def approve_return(
    db: Session, return_id: int, user_id: int | None = None
) -> DevolucaoVenda:
    record = get_return(db, return_id)
    if record is None:
        raise SalesStockConflict("Devolução não encontrada.")
    if record.status == "APROVADA":
        return record
    if record.status != "RASCUNHO":
        raise SalesStockConflict("Somente devolução em rascunho pode ser aprovada.")
    sale = get_sale(db, record.venda_id)
    if sale is None:
        raise SalesStockConflict("Venda da devolução não encontrada.")
    try:
        try:
            default_deposit = get_default_deposit(db)
        except InventoryNotFound as exception:
            raise SalesStockConflict(str(exception)) from None
        for item in record.itens:
            sale_item = db.get(VendaItem, item.venda_item_id)
            if sale_item is None:
                raise SalesStockConflict("Item da venda não encontrado.")
            returned = db.scalar(
                select(DevolucaoVendaItem.quantidade)
                .join(DevolucaoVenda)
                .where(
                    DevolucaoVendaItem.venda_item_id == item.venda_item_id,
                    DevolucaoVendaItem.devolucao_id != record.id,
                    DevolucaoVenda.status == "APROVADA",
                )
            ) or 0
            if item.quantidade + returned > sale_item.quantidade:
                raise SalesStockConflict(
                    "A quantidade devolvida excede a quantidade vendida."
                )
            create_movement(
                db,
                StockMovementCreate(
                    produto_id=item.produto_id,
                    deposito_id=default_deposit.id,
                    tipo="ENTRADA",
                    quantidade=item.quantidade,
                    data_movimentacao=datetime.now(timezone.utc),
                    origem="DEVOLUCAO_VENDA",
                    documento_tipo="DEVOLUCAO_VENDA",
                    documento_id=record.id,
                    chave_idempotencia=f"DEVOLUCAO-VENDA-{record.id}-{item.id}",
                ),
                user_id=user_id,
                commit=False,
            )
        record.status = "APROVADA"
        db.commit()
    except SalesStockConflict:
        db.rollback()
        raise
    return get_return(db, record.id)  # type: ignore[return-value]


def return_to_read(record: DevolucaoVenda):
    from app.schemas.returns import ReturnItemRead, ReturnRead

    return ReturnRead(
        id=record.id,
        venda_id=record.venda_id,
        status=record.status,
        motivo=record.motivo,
        usuario_id=record.usuario_id,
        created_at=record.created_at,
        updated_at=record.updated_at,
        itens=[ReturnItemRead.model_validate(item) for item in record.itens],
    )
