from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models import Cliente, Funcionario, Produto, Venda, VendaItem
from app.schemas.sales import (
    ClienteResumo,
    FornecedorResumo,
    FuncionarioResumo,
    ProdutoResumo,
    VendaCancel,
    VendaCreate,
    VendaItemRead,
    VendaRead,
)

MONEY_QUANTUM = Decimal("0.01")


class SaleReferenceNotFound(Exception):
    """Indica uma referência de venda inexistente."""


class SaleEmployeeInactive(Exception):
    """Indica que um funcionário inativo tentou iniciar uma venda."""


class SalePersistenceError(Exception):
    """Indica falha controlada ao persistir uma venda."""


class SaleNotFound(Exception):
    """Indica uma venda inexistente durante uma operação de venda."""


def cancel_sale(db: Session, sale_id: int, payload: VendaCancel) -> Venda:
    sale = get_sale(db, sale_id)
    if sale is None:
        raise SaleNotFound("Venda não encontrada.")
    if sale.status == "CANCELADA":
        return sale

    sale.status = "CANCELADA"
    sale.cancelada_em = datetime.now(timezone.utc)
    sale.motivo_cancelamento = payload.motivo
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    cancelled_sale = get_sale(db, sale.id)
    if cancelled_sale is None:
        raise SalePersistenceError
    return cancelled_sale


def calculate_subtotal(quantity: Decimal, unit_price: Decimal) -> Decimal:
    return (quantity * unit_price).quantize(
        MONEY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def sale_query():
    return select(Venda).options(
        selectinload(Venda.cliente),
        selectinload(Venda.funcionario),
        selectinload(Venda.itens).options(
            selectinload(VendaItem.produto),
            selectinload(VendaItem.fornecedor),
        ),
    )


def get_sale(db: Session, sale_id: int) -> Venda | None:
    return db.scalar(sale_query().where(Venda.id == sale_id))


def create_sale(db: Session, payload: VendaCreate) -> Venda:
    customer = db.get(Cliente, payload.cliente_id)
    if customer is None:
        raise SaleReferenceNotFound("Cliente não encontrado.")

    employee = db.get(Funcionario, payload.funcionario_id)
    if employee is None:
        raise SaleReferenceNotFound("Funcionário não encontrado.")
    if not employee.ativo:
        raise SaleEmployeeInactive(
            "Funcionário inativo não pode realizar novas vendas."
        )

    product_ids = [item.produto_id for item in payload.itens]
    products = {
        product.id: product
        for product in db.scalars(
            select(Produto).where(Produto.id.in_(product_ids))
        ).all()
    }
    for product_id in product_ids:
        if product_id not in products:
            raise SaleReferenceNotFound("Produto não encontrado.")

    sale = Venda(
        cliente_id=customer.id,
        funcionario_id=employee.id,
        data_venda=payload.data_venda,
        observacao=payload.observacao,
    )
    for item_payload in payload.itens:
        product = products[item_payload.produto_id]
        sale.itens.append(
            VendaItem(
                produto_id=product.id,
                quantidade=item_payload.quantidade,
                preco_unitario=product.preco_venda,
                fornecedor_id=product.fornecedor_id,
            )
        )

    db.add(sale)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise SalePersistenceError from None
    except Exception:
        db.rollback()
        raise

    persisted_sale = get_sale(db, sale.id)
    if persisted_sale is None:
        raise SalePersistenceError
    return persisted_sale


def sale_to_read(sale: Venda) -> VendaRead:
    items: list[VendaItemRead] = []
    for item in sale.itens:
        items.append(
            VendaItemRead(
                id=item.id,
                produto=ProdutoResumo.model_validate(item.produto),
                fornecedor_id=item.fornecedor_id,
                fornecedor=FornecedorResumo.model_validate(item.fornecedor),
                quantidade=item.quantidade,
                preco_unitario=item.preco_unitario,
                subtotal=calculate_subtotal(
                    item.quantidade,
                    item.preco_unitario,
                ),
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
        )

    total = sum((item.subtotal for item in items), Decimal("0.00"))
    return VendaRead(
        id=sale.id,
        data_venda=sale.data_venda,
        status=sale.status,
        cancelada_em=sale.cancelada_em,
        motivo_cancelamento=sale.motivo_cancelamento,
        observacao=sale.observacao,
        created_at=sale.created_at,
        updated_at=sale.updated_at,
        cliente=ClienteResumo.model_validate(sale.cliente),
        funcionario=FuncionarioResumo.model_validate(sale.funcionario),
        itens=items,
        total=total,
    )
