"""Regras de estado, cálculo e conversão dos documentos comerciais."""

from decimal import ROUND_HALF_UP, Decimal
from html import escape
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Cliente,
    CondicaoPagamento,
    Funcionario,
    Orcamento,
    OrcamentoItem,
    PedidoVenda,
    PedidoVendaItem,
    Produto,
    Venda,
    VendaItem,
)
from app.schemas.commercial import (
    CommercialItemCreate,
    CommercialItemRead,
    OrderCreate,
    OrderRead,
    OrderStatus,
    OrderUpdate,
    QuoteCreate,
    QuoteRead,
    QuoteStatus,
    QuoteUpdate,
)
from app.schemas.sales import VendaRead
from app.services.sales import get_sale, sale_to_read

MONEY_QUANTUM = Decimal("0.01")

QUOTE_TRANSITIONS: dict[QuoteStatus, frozenset[QuoteStatus]] = {
    "RASCUNHO": frozenset({"ENVIADO", "CANCELADO"}),
    "ENVIADO": frozenset({"APROVADO", "RECUSADO", "EXPIRADO", "CANCELADO"}),
    "APROVADO": frozenset({"CANCELADO"}),
    "RECUSADO": frozenset(),
    "EXPIRADO": frozenset(),
    "CANCELADO": frozenset(),
}
ORDER_TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    "RASCUNHO": frozenset({"CONFIRMADO", "CANCELADO"}),
    "CONFIRMADO": frozenset({"CONCLUIDO", "CANCELADO"}),
    "CONCLUIDO": frozenset({"CANCELADO"}),
    "CANCELADO": frozenset(),
}


class CommercialNotFound(Exception):
    """Referência comercial inexistente."""


class CommercialConflict(Exception):
    """Conflito de estado ou persistência comercial."""


class CommercialValidationError(Exception):
    """Dados comerciais inválidos para o domínio."""


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def line_total(
    quantity: Decimal,
    unit_price: Decimal,
    discount: Decimal,
    surcharge: Decimal,
) -> Decimal:
    return money(quantity * unit_price - discount + surcharge)


def document_totals(items) -> tuple[Decimal, Decimal]:
    subtotal = money(
        sum(
            (money(item.quantidade * item.preco_unitario) for item in items),
            Decimal("0.00"),
        )
    )
    adjustments = sum(
        (item.desconto - item.acrescimo for item in items), Decimal("0.00")
    )
    return subtotal, money(subtotal - adjustments)


def total_with_document_adjustments(document, items) -> tuple[Decimal, Decimal]:
    subtotal = money(
        sum(
            (money(item.quantidade * item.preco_unitario) for item in items),
            Decimal("0.00"),
        )
    )
    items_total = money(
        sum(
            (
                line_total(
                    item.quantidade,
                    item.preco_unitario,
                    item.desconto,
                    item.acrescimo,
                )
                for item in items
            ),
            Decimal("0.00"),
        )
    )
    total = money(
        items_total - document.desconto + document.acrescimo + document.frete
    )
    return subtotal, total


def ensure_references(
    db: Session,
    customer_id: int,
    employee_id: int | None,
    payment_condition_id: int | None,
) -> tuple[Cliente, Funcionario | None, CondicaoPagamento | None]:
    customer = db.get(Cliente, customer_id)
    if customer is None:
        raise CommercialNotFound("Cliente não encontrado.")
    employee = db.get(Funcionario, employee_id) if employee_id else None
    if employee_id and employee is None:
        raise CommercialNotFound("Funcionário não encontrado.")
    condition = (
        db.get(CondicaoPagamento, payment_condition_id)
        if payment_condition_id
        else None
    )
    if payment_condition_id and (condition is None or not condition.ativo):
        raise CommercialNotFound("Condição de pagamento não encontrada.")
    return customer, employee, condition


def snapshot_products(
    db: Session, items: list[CommercialItemCreate]
) -> list[dict[str, object]]:
    product_ids = [item.produto_id for item in items]
    if len(product_ids) != len(set(product_ids)):
        raise CommercialValidationError(
            "O mesmo produto não pode aparecer mais de uma vez."
        )
    products = {
        product.id: product
        for product in db.scalars(
            select(Produto).options(selectinload(Produto.fornecedor)).where(
                Produto.id.in_(product_ids)
            )
        ).all()
    }
    snapshots: list[dict[str, object]] = []
    for item in items:
        product = products.get(item.produto_id)
        if product is None:
            raise CommercialNotFound("Produto não encontrado.")
        if not product.ativo:
            raise CommercialValidationError(
                "Produto inativo não pode entrar em novo documento comercial."
            )
        snapshots.append(
            {
                "produto_id": product.id,
                "produto_nome": product.nome,
                "sku": product.sku,
                "fornecedor_id": product.fornecedor_id,
                "fornecedor_nome": product.fornecedor.nome,
                "quantidade": item.quantidade,
                "preco_unitario": item.preco_unitario
                if item.preco_unitario is not None
                else product.preco_venda,
                "desconto": item.desconto,
                "acrescimo": item.acrescimo,
            }
        )
    return snapshots


def quote_query():
    return select(Orcamento).options(
        selectinload(Orcamento.itens), selectinload(Orcamento.pedido)
    )


def order_query():
    return select(PedidoVenda).options(selectinload(PedidoVenda.itens))


def create_quote(db: Session, payload: QuoteCreate) -> Orcamento:
    ensure_references(
        db,
        payload.cliente_id,
        payload.funcionario_id,
        payload.condicao_pagamento_id,
    )
    snapshots = snapshot_products(db, payload.itens)
    quote = Orcamento(
        numero=payload.numero or f"ORC-{uuid4().hex[:12].upper()}",
        cliente_id=payload.cliente_id,
        funcionario_id=payload.funcionario_id,
        condicao_pagamento_id=payload.condicao_pagamento_id,
        validade=payload.validade,
        desconto=payload.desconto,
        acrescimo=payload.acrescimo,
        frete=payload.frete,
        observacao=payload.observacao,
        itens=[OrcamentoItem(**snapshot) for snapshot in snapshots],
    )
    db.add(quote)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise CommercialConflict("Número de orçamento já cadastrado.") from None
    return get_quote(db, quote.id)  # type: ignore[return-value]


def create_order(db: Session, payload: OrderCreate) -> PedidoVenda:
    ensure_references(
        db,
        payload.cliente_id,
        payload.funcionario_id,
        payload.condicao_pagamento_id,
    )
    if payload.orcamento_id is not None:
        quote = get_quote(db, payload.orcamento_id)
        if quote is None:
            raise CommercialNotFound("Orçamento não encontrado.")
        if quote.status != "APROVADO":
            raise CommercialConflict("Somente orçamento aprovado pode gerar pedido.")
        if quote.pedido is not None:
            raise CommercialConflict("Este orçamento já foi convertido em pedido.")
        snapshots = [
            {
                "produto_id": item.produto_id,
                "produto_nome": item.produto_nome,
                "sku": item.sku,
                "fornecedor_id": item.fornecedor_id,
                "fornecedor_nome": item.fornecedor_nome,
                "quantidade": item.quantidade,
                "preco_unitario": item.preco_unitario,
                "desconto": item.desconto,
                "acrescimo": item.acrescimo,
            }
            for item in quote.itens
        ]
        payload_data = {
            "cliente_id": quote.cliente_id,
            "funcionario_id": quote.funcionario_id,
            "condicao_pagamento_id": quote.condicao_pagamento_id,
            "desconto": quote.desconto,
            "acrescimo": quote.acrescimo,
            "frete": quote.frete,
            "observacao": quote.observacao,
        }
        quote_id = quote.id
    else:
        snapshots = snapshot_products(db, payload.itens)
        payload_data = payload.model_dump(
            exclude={"numero", "orcamento_id", "itens"}
        )
        quote_id = None
    order = PedidoVenda(
        numero=payload.numero or f"PED-{uuid4().hex[:12].upper()}",
        orcamento_id=quote_id,
        itens=[PedidoVendaItem(**snapshot) for snapshot in snapshots],
        **payload_data,
    )
    db.add(order)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise CommercialConflict("Número de pedido já cadastrado.") from None
    return get_order(db, order.id)  # type: ignore[return-value]


def _replace_document_items(
    document, item_class, snapshots: list[dict[str, object]]
) -> None:
    document.itens.clear()
    document.itens.extend(item_class(**snapshot) for snapshot in snapshots)


def update_quote(db: Session, quote_id: int, payload: QuoteUpdate) -> Orcamento:
    quote = get_quote(db, quote_id)
    if quote is None:
        raise CommercialNotFound("Orçamento não encontrado.")
    if quote.status != "RASCUNHO" or quote.pedido is not None:
        raise CommercialConflict(
            "Somente orçamento em rascunho e sem pedido pode ser editado."
        )
    data = payload.model_dump(exclude_unset=True)
    if payload.itens is not None:
        snapshots = snapshot_products(db, payload.itens)
        _replace_document_items(quote, OrcamentoItem, snapshots)
        data.pop("itens", None)
    ensure_references(
        db,
        data.get("cliente_id", quote.cliente_id),
        data.get("funcionario_id", quote.funcionario_id),
        data.get("condicao_pagamento_id", quote.condicao_pagamento_id),
    )
    for field, value in data.items():
        setattr(quote, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise CommercialConflict("Número de orçamento já cadastrado.") from None
    return get_quote(db, quote.id)  # type: ignore[return-value]


def update_order(db: Session, order_id: int, payload: OrderUpdate) -> PedidoVenda:
    order = get_order(db, order_id)
    if order is None:
        raise CommercialNotFound("Pedido não encontrado.")
    if order.status != "RASCUNHO" or order.venda_id is not None:
        raise CommercialConflict(
            "Somente pedido em rascunho e sem venda pode ser editado."
        )
    data = payload.model_dump(exclude_unset=True)
    if payload.itens is not None:
        snapshots = snapshot_products(db, payload.itens)
        _replace_document_items(order, PedidoVendaItem, snapshots)
        data.pop("itens", None)
    ensure_references(
        db,
        data.get("cliente_id", order.cliente_id),
        data.get("funcionario_id", order.funcionario_id),
        data.get("condicao_pagamento_id", order.condicao_pagamento_id),
    )
    for field, value in data.items():
        setattr(order, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise CommercialConflict("Número de pedido já cadastrado.") from None
    return get_order(db, order.id)  # type: ignore[return-value]


def get_quote(db: Session, quote_id: int) -> Orcamento | None:
    return db.scalar(quote_query().where(Orcamento.id == quote_id))


def get_order(db: Session, order_id: int) -> PedidoVenda | None:
    return db.scalar(order_query().where(PedidoVenda.id == order_id))


def change_quote_status(
    db: Session, quote_id: int, status: QuoteStatus
) -> Orcamento:
    quote = get_quote(db, quote_id)
    if quote is None:
        raise CommercialNotFound("Orçamento não encontrado.")
    if status != quote.status and status not in QUOTE_TRANSITIONS[quote.status]:
        raise CommercialConflict(
            f"Transição de orçamento {quote.status} para {status} não permitida."
        )
    quote.status = status
    db.commit()
    return get_quote(db, quote.id)  # type: ignore[return-value]


def change_order_status(db: Session, order_id: int, status: OrderStatus) -> PedidoVenda:
    order = get_order(db, order_id)
    if order is None:
        raise CommercialNotFound("Pedido não encontrado.")
    if status != order.status and status not in ORDER_TRANSITIONS[order.status]:
        raise CommercialConflict(
            f"Transição de pedido {order.status} para {status} não permitida."
        )
    order.status = status
    db.commit()
    return get_order(db, order.id)  # type: ignore[return-value]


def convert_quote_to_order(db: Session, quote_id: int) -> PedidoVenda:
    quote = get_quote(db, quote_id)
    if quote is None:
        raise CommercialNotFound("Orçamento não encontrado.")
    if quote.status != "APROVADO":
        raise CommercialConflict("Somente orçamento aprovado pode gerar pedido.")
    if quote.pedido is not None:
        return get_order(db, quote.pedido.id)  # type: ignore[return-value]
    payload = OrderCreate(
        cliente_id=quote.cliente_id,
        funcionario_id=quote.funcionario_id,
        orcamento_id=quote.id,
        condicao_pagamento_id=quote.condicao_pagamento_id,
        itens=[
            CommercialItemCreate(
                produto_id=item.produto_id,
                quantidade=item.quantidade,
                preco_unitario=item.preco_unitario,
                desconto=item.desconto,
                acrescimo=item.acrescimo,
            )
            for item in quote.itens
        ],
    )
    return create_order(db, payload)


def convert_order_to_sale(db: Session, order_id: int) -> VendaRead:
    order = get_order(db, order_id)
    if order is None:
        raise CommercialNotFound("Pedido não encontrado.")
    if order.status not in {"CONFIRMADO", "CONCLUIDO"}:
        raise CommercialConflict(
            "Somente pedido confirmado ou concluído pode gerar venda."
        )
    if order.funcionario_id is None:
        raise CommercialConflict(
            "O pedido precisa de funcionário responsável para gerar venda."
        )
    employee = db.get(Funcionario, order.funcionario_id)
    if employee is None or not employee.ativo:
        raise CommercialConflict(
            "O funcionário do pedido não está disponível para gerar venda."
        )
    if order.venda_id is not None:
        sale = get_sale(db, order.venda_id)
        if sale is None:
            raise CommercialConflict("O vínculo da venda do pedido está inconsistente.")
        return sale_to_read(sale)
    sale = Venda(
        cliente_id=order.cliente_id,
        funcionario_id=order.funcionario_id,
        data_venda=order.created_at,
        pedido_venda_id=order.id,
        condicao_pagamento_id=order.condicao_pagamento_id,
        observacao=order.observacao,
        itens=[
            VendaItem(
                produto_id=item.produto_id,
                quantidade=item.quantidade,
                preco_unitario=item.preco_unitario,
                fornecedor_id=item.fornecedor_id,
            )
            for item in order.itens
        ],
    )
    db.add(sale)
    try:
        db.flush()
        order.venda_id = sale.id
        db.commit()
    except IntegrityError:
        db.rollback()
        raise CommercialConflict(
            "Não foi possível converter o pedido em venda."
        ) from None
    persisted = get_sale(db, sale.id)
    if persisted is None:
        raise CommercialConflict("Venda convertida não encontrada.")
    return sale_to_read(persisted)


def item_read(item) -> CommercialItemRead:
    return CommercialItemRead(
        id=item.id,
        produto_id=item.produto_id,
        produto_nome=item.produto_nome,
        sku=item.sku,
        fornecedor_id=item.fornecedor_id,
        fornecedor_nome=item.fornecedor_nome,
        quantidade=item.quantidade,
        preco_unitario=item.preco_unitario,
        desconto=item.desconto,
        acrescimo=item.acrescimo,
        total=line_total(
            item.quantidade, item.preco_unitario, item.desconto, item.acrescimo
        ),
    )


def quote_to_read(quote: Orcamento) -> QuoteRead:
    subtotal, total = total_with_document_adjustments(quote, quote.itens)
    return QuoteRead(
        id=quote.id,
        numero=quote.numero,
        cliente_id=quote.cliente_id,
        funcionario_id=quote.funcionario_id,
        condicao_pagamento_id=quote.condicao_pagamento_id,
        validade=quote.validade,
        desconto=quote.desconto,
        acrescimo=quote.acrescimo,
        frete=quote.frete,
        status=quote.status,
        observacao=quote.observacao,
        created_at=quote.created_at,
        updated_at=quote.updated_at,
        itens=[item_read(item) for item in quote.itens],
        subtotal=subtotal,
        total=total,
        pedido_id=quote.pedido.id if quote.pedido else None,
    )


def order_to_read(order: PedidoVenda) -> OrderRead:
    subtotal, total = total_with_document_adjustments(order, order.itens)
    return OrderRead(
        id=order.id,
        numero=order.numero,
        cliente_id=order.cliente_id,
        funcionario_id=order.funcionario_id,
        orcamento_id=order.orcamento_id,
        venda_id=order.venda_id,
        condicao_pagamento_id=order.condicao_pagamento_id,
        desconto=order.desconto,
        acrescimo=order.acrescimo,
        frete=order.frete,
        status=order.status,
        observacao=order.observacao,
        created_at=order.created_at,
        updated_at=order.updated_at,
        itens=[item_read(item) for item in order.itens],
        subtotal=subtotal,
        total=total,
    )


def document_html(title: str, document, items) -> str:
    _, total = total_with_document_adjustments(document, items)

    def render_item(item) -> str:
        item_total = line_total(
            item.quantidade,
            item.preco_unitario,
            item.desconto,
            item.acrescimo,
        )
        return (
            "<tr>"
            f"<td>{escape(item.sku)}</td>"
            f"<td>{escape(item.produto_nome)}</td>"
            f"<td>{item.quantidade}</td>"
            f"<td>R$ {money(item.preco_unitario):.2f}</td>"
            f"<td>R$ {item_total:.2f}</td>"
            "</tr>"
        )

    rows = "".join(render_item(item) for item in items)
    return (
        "<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>"
        f"<title>{escape(title)} {escape(document.numero)}</title>"
        "<style>body{font-family:Arial,sans-serif;margin:40px;color:#172033}"
        "table{border-collapse:collapse;width:100%;margin-top:24px}"
        "th,td{border-bottom:1px solid #d8dee8;padding:10px;text-align:left}"
        ".total{text-align:right;font-size:20px;font-weight:bold;margin-top:24px}"
        "</style></head><body>"
        f"<h1>{escape(title)}</h1><p>Número: {escape(document.numero)}</p>"
        f"<p>Status: {escape(document.status)}</p><table><thead><tr>"
        "<th>SKU</th><th>Produto</th><th>Quantidade</th><th>Unitário</th>"
        f"<th>Total</th></tr></thead><tbody>{rows}</tbody></table>"
        f"<p class='total'>Total: R$ {total:.2f}</p></body></html>"
    )
