from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, desc, func, literal, select
from sqlalchemy.orm import Session, aliased, selectinload

from app.api.dependencies import require_authenticated
from app.db.session import get_db_session
from app.models import (
    Cliente,
    DepositoEstoque,
    DevolucaoVenda,
    LiquidacaoFinanceira,
    MovimentacaoEstoque,
    Orcamento,
    ParcelaFinanceira,
    PedidoCompra,
    PedidoCompraItem,
    Produto,
    RecebimentoCompra,
    RecebimentoCompraItem,
    TituloFinanceiro,
    Venda,
    VendaItem,
)
from app.schemas.dashboard import (
    DashboardAnalyticsGranularity,
    DashboardAnalyticsPeriod,
    DashboardAnalyticsRead,
)
from app.services.finance import cashflow_summary
from app.services.inventory import (
    NEGATIVE_TYPES,
    POSITIVE_TYPES,
    InventoryNotFound,
    get_default_deposit,
    list_balances,
)

router = APIRouter(
    prefix="/api/reports",
    tags=["reports"],
    dependencies=[Depends(require_authenticated)],
)


def date_filters(query, column, date_from: date | None, date_to: date | None):
    if date_from is not None:
        query = query.where(
            column >= datetime.combine(date_from, time.min, tzinfo=timezone.utc)
        )
    if date_to is not None:
        query = query.where(
            column
            < datetime.combine(
                date_to + timedelta(days=1), time.min, tzinfo=timezone.utc
            )
        )
    return query


_DASHBOARD_PERIODS: dict[
    DashboardAnalyticsPeriod, tuple[int, DashboardAnalyticsGranularity]
] = {
    "30d": (30, "day"),
    "90d": (90, "week"),
    "6m": (183, "month"),
    "12m": (365, "month"),
}


def _dashboard_period(
    period: DashboardAnalyticsPeriod,
) -> tuple[date, date, DashboardAnalyticsGranularity]:
    days, granularity = _DASHBOARD_PERIODS[period]
    date_to = date.today()
    return date_to - timedelta(days=days - 1), date_to, granularity


def _bucket_start(value: date, granularity: DashboardAnalyticsGranularity) -> date:
    if granularity == "day":
        return value
    if granularity == "week":
        return value - timedelta(days=value.weekday())
    return value.replace(day=1)


def _next_bucket(value: date, granularity: DashboardAnalyticsGranularity) -> date:
    if granularity == "day":
        return value + timedelta(days=1)
    if granularity == "week":
        return value + timedelta(days=7)
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def _dashboard_buckets(
    date_from: date,
    date_to: date,
    granularity: DashboardAnalyticsGranularity,
) -> list[date]:
    current = _bucket_start(date_from, granularity)
    last = _bucket_start(date_to, granularity)
    buckets: list[date] = []
    while current <= last:
        buckets.append(current)
        current = _next_bucket(current, granularity)
    return buckets


def _bucket_date(value: date | datetime) -> date:
    return value.date() if isinstance(value, datetime) else value


def _utc_bucket(column, granularity: DashboardAnalyticsGranularity):
    return func.date_trunc(granularity, func.timezone("UTC", column))


def _confirmed_settlements_by_installment():
    return (
        select(
            LiquidacaoFinanceira.parcela_id.label("parcela_id"),
            func.sum(LiquidacaoFinanceira.valor).label("settled"),
        )
        .where(LiquidacaoFinanceira.status == "CONFIRMADA")
        .group_by(LiquidacaoFinanceira.parcela_id)
        .subquery()
    )


def _open_installment_value(settled_by_installment):
    settled_value = func.coalesce(
        settled_by_installment.c.settled, literal(Decimal("0.00"))
    )
    return case(
        (
            ParcelaFinanceira.valor > settled_value,
            ParcelaFinanceira.valor - settled_value,
        ),
        else_=literal(Decimal("0.00")),
    )


def _finance_commitment_trend(
    db: Session,
    date_from: date,
    date_to: date,
    granularity: DashboardAnalyticsGranularity,
) -> list[dict[str, date | float]]:
    buckets = _dashboard_buckets(date_from, date_to, granularity)
    settled_by_installment = _confirmed_settlements_by_installment()
    open_value = _open_installment_value(settled_by_installment)
    finance_bucket = func.date_trunc(granularity, ParcelaFinanceira.vencimento)
    finance_rows = db.execute(
        select(finance_bucket, TituloFinanceiro.tipo, func.sum(open_value))
        .join(
            TituloFinanceiro,
            TituloFinanceiro.id == ParcelaFinanceira.titulo_id,
        )
        .outerjoin(
            settled_by_installment,
            settled_by_installment.c.parcela_id == ParcelaFinanceira.id,
        )
        .where(
            ParcelaFinanceira.vencimento >= date_from,
            ParcelaFinanceira.vencimento <= date_to,
        )
        .group_by(finance_bucket, TituloFinanceiro.tipo)
        .order_by(finance_bucket)
    ).all()
    finance_by_bucket: dict[date, dict[str, Decimal]] = {}
    for bucket, title_type, amount in finance_rows:
        values = finance_by_bucket.setdefault(
            _bucket_date(bucket), {"RECEBER": Decimal("0.00"), "PAGAR": Decimal("0.00")}
        )
        values[title_type] += amount or Decimal("0.00")

    return [
        {
            "bucket": bucket,
            "receivable": float(
                finance_by_bucket.get(bucket, {}).get("RECEBER", Decimal("0.00"))
            ),
            "payable": float(
                finance_by_bucket.get(bucket, {}).get("PAGAR", Decimal("0.00"))
            ),
        }
        for bucket in buckets
    ]


def _overdue_open_summary(db: Session) -> dict[str, int | float]:
    settled_by_installment = _confirmed_settlements_by_installment()
    open_value = _open_installment_value(settled_by_installment)
    rows = db.execute(
        select(
            TituloFinanceiro.tipo,
            func.count(ParcelaFinanceira.id),
            func.sum(open_value),
        )
        .join(
            TituloFinanceiro,
            TituloFinanceiro.id == ParcelaFinanceira.titulo_id,
        )
        .outerjoin(
            settled_by_installment,
            settled_by_installment.c.parcela_id == ParcelaFinanceira.id,
        )
        .where(
            ParcelaFinanceira.vencimento < date.today(),
            open_value > 0,
        )
        .group_by(TituloFinanceiro.tipo)
    ).all()
    summary = {
        "overdue_open_installments": 0,
        "overdue_receivable": 0.0,
        "overdue_payable": 0.0,
    }
    for title_type, installment_count, amount in rows:
        summary["overdue_open_installments"] += installment_count or 0
        key = "overdue_receivable" if title_type == "RECEBER" else "overdue_payable"
        summary[key] = float(amount or Decimal("0.00"))
    return summary


def _stock_movement_trend(
    db: Session,
    deposit_id: int,
    date_from: date,
    date_to: date,
    granularity: DashboardAnalyticsGranularity,
) -> list[dict[str, date | int]]:
    buckets = _dashboard_buckets(date_from, date_to, granularity)
    start_datetime = datetime.combine(date_from, time.min, tzinfo=timezone.utc)
    end_datetime = datetime.combine(
        date_to + timedelta(days=1), time.min, tzinfo=timezone.utc
    )
    reverse_source = aliased(MovimentacaoEstoque)
    entry_event = case(
        (MovimentacaoEstoque.tipo.in_(POSITIVE_TYPES), 1),
        (
            (MovimentacaoEstoque.tipo == "REVERSAO")
            & reverse_source.tipo.in_(NEGATIVE_TYPES),
            1,
        ),
        else_=0,
    )
    exit_event = case(
        (MovimentacaoEstoque.tipo.in_(NEGATIVE_TYPES), 1),
        (
            (MovimentacaoEstoque.tipo == "REVERSAO")
            & reverse_source.tipo.in_(POSITIVE_TYPES),
            1,
        ),
        else_=0,
    )
    movement_bucket = _utc_bucket(MovimentacaoEstoque.data_movimentacao, granularity)
    rows = db.execute(
        select(
            movement_bucket,
            func.sum(entry_event),
            func.sum(exit_event),
        )
        .outerjoin(
            reverse_source,
            reverse_source.id == MovimentacaoEstoque.movimento_origem_id,
        )
        .where(
            MovimentacaoEstoque.deposito_id == deposit_id,
            MovimentacaoEstoque.data_movimentacao >= start_datetime,
            MovimentacaoEstoque.data_movimentacao < end_datetime,
        )
        .group_by(movement_bucket)
        .order_by(movement_bucket)
    ).all()
    movements_by_bucket = {
        _bucket_date(bucket): (int(entries or 0), int(exits or 0))
        for bucket, entries, exits in rows
    }
    return [
        {
            "bucket": bucket,
            "entries": movements_by_bucket.get(bucket, (0, 0))[0],
            "exits": movements_by_bucket.get(bucket, (0, 0))[1],
        }
        for bucket in buckets
    ]


def _commercial_granularity(date_from: date, date_to: date) -> str:
    span_days = (date_to - date_from).days + 1
    if span_days <= 45:
        return "day"
    if span_days <= 180:
        return "week"
    return "month"


@router.get("/commercial")
def commercial_report(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db_session),
):
    sales_query = date_filters(select(Venda), Venda.data_venda, date_from, date_to)
    sales = db.scalars(sales_query).all()
    customer_total = func.sum(VendaItem.quantidade * VendaItem.preco_unitario)
    by_customer = db.execute(
        date_filters(
            select(
                Venda.cliente_id,
                Cliente.nome,
                func.count(Venda.id),
                customer_total,
            )
            .join(VendaItem, VendaItem.venda_id == Venda.id)
            .outerjoin(Cliente, Cliente.id == Venda.cliente_id)
            .where(Venda.status == "CONCLUIDA")
            .group_by(Venda.cliente_id, Cliente.nome)
            .order_by(desc(customer_total), Venda.cliente_id),
            Venda.data_venda,
            date_from,
            date_to,
        )
    ).all()
    product_quantity = func.sum(VendaItem.quantidade)
    product_total = func.sum(VendaItem.quantidade * VendaItem.preco_unitario)
    by_product = db.execute(
        date_filters(
            select(
                VendaItem.produto_id,
                Produto.nome,
                product_quantity,
                product_total,
            )
            .join(Venda, Venda.id == VendaItem.venda_id)
            .join(Produto, Produto.id == VendaItem.produto_id)
            .where(Venda.status == "CONCLUIDA")
            .group_by(VendaItem.produto_id, Produto.nome)
            .order_by(desc(product_total), VendaItem.produto_id),
            Venda.data_venda,
            date_from,
            date_to,
        )
    ).all()
    completed_date_range = db.execute(
        date_filters(
            select(func.min(Venda.data_venda), func.max(Venda.data_venda)).where(
                Venda.status == "CONCLUIDA"
            ),
            Venda.data_venda,
            date_from,
            date_to,
        )
    ).one()
    first_completed_at, last_completed_at = completed_date_range
    if first_completed_at is not None and last_completed_at is not None:
        temporal_from = date_from or _bucket_date(first_completed_at)
        temporal_to = date_to or _bucket_date(last_completed_at)
        granularity = _commercial_granularity(temporal_from, temporal_to)
        buckets = _dashboard_buckets(temporal_from, temporal_to, granularity)
        sales_bucket = _utc_bucket(Venda.data_venda, granularity)
        sales_rows = db.execute(
            date_filters(
                select(
                    sales_bucket,
                    func.sum(VendaItem.quantidade * VendaItem.preco_unitario),
                    func.count(func.distinct(Venda.id)),
                )
                .join(VendaItem, VendaItem.venda_id == Venda.id)
                .where(Venda.status == "CONCLUIDA")
                .group_by(sales_bucket)
                .order_by(sales_bucket),
                Venda.data_venda,
                date_from,
                date_to,
            )
        ).all()
        sales_by_bucket = {
            _bucket_date(row[0]): (row[1] or Decimal("0.00"), row[2] or 0)
            for row in sales_rows
        }
        sales_trend = [
            {
                "bucket": bucket,
                "sales_value": float(
                    sales_by_bucket.get(bucket, (Decimal("0.00"), 0))[0]
                ),
                "completed_sales": sales_by_bucket.get(bucket, (Decimal("0.00"), 0))[1],
            }
            for bucket in buckets
        ]
    else:
        granularity = "month"
        sales_trend = []
    returns = (
        db.scalar(
            select(func.count(DevolucaoVenda.id)).where(
                DevolucaoVenda.status == "APROVADA"
            )
        )
        or 0
    )
    return {
        "sales": len(sales),
        "completed_sales": sum(sale.status == "CONCLUIDA" for sale in sales),
        "cancelled_sales": sum(sale.status == "CANCELADA" for sale in sales),
        "approved_returns": returns,
        "granularity": granularity,
        "sales_trend": sales_trend,
        "by_customer": [
            {
                "customer_id": row[0],
                "customer_name": row[1],
                "sales": row[2],
                "total": row[3] or Decimal("0"),
            }
            for row in by_customer
        ],
        "by_product": [
            {
                "product_id": row[0],
                "product_name": row[1],
                "quantity": row[2] or Decimal("0"),
                "total": row[3] or Decimal("0"),
            }
            for row in by_product
        ],
    }


@router.get("/purchases")
def purchases_report(
    period: DashboardAnalyticsPeriod = Query(default="12m"),
    db: Session = Depends(get_db_session),
):
    date_from, date_to, _ = _dashboard_period(period)
    start_datetime = datetime.combine(date_from, time.min, tzinfo=timezone.utc)
    end_datetime = datetime.combine(
        date_to + timedelta(days=1), time.min, tzinfo=timezone.utc
    )
    status_values = (
        "RASCUNHO",
        "EMITIDO",
        "PARCIALMENTE_RECEBIDO",
        "RECEBIDO",
        "CANCELADO",
    )
    receiving_statuses = ("EMITIDO", "PARCIALMENTE_RECEBIDO")
    status_rows = db.execute(
        select(PedidoCompra.status, func.count(PedidoCompra.id)).group_by(
            PedidoCompra.status
        )
    ).all()
    total_orders = db.scalar(select(func.count(PedidoCompra.id))) or 0
    status_counts = {
        status: next((count for value, count in status_rows if value == status), 0)
        for status in status_values
    }
    period_order_count = (
        db.scalar(
            select(func.count(PedidoCompra.id)).where(
                PedidoCompra.created_at >= start_datetime,
                PedidoCompra.created_at < end_datetime,
            )
        )
        or 0
    )
    ordered_value_in_period = db.scalar(
        select(func.sum(PedidoCompraItem.quantidade * PedidoCompraItem.custo_unitario))
        .join(PedidoCompra, PedidoCompra.id == PedidoCompraItem.pedido_id)
        .where(
            PedidoCompra.created_at >= start_datetime,
            PedidoCompra.created_at < end_datetime,
            PedidoCompra.status != "CANCELADO",
        )
    ) or Decimal("0.00")
    pending_value = db.scalar(
        select(
            func.sum(
                (PedidoCompraItem.quantidade - PedidoCompraItem.quantidade_recebida)
                * PedidoCompraItem.custo_unitario
            )
        )
        .join(PedidoCompra, PedidoCompra.id == PedidoCompraItem.pedido_id)
        .where(
            PedidoCompra.status.in_(receiving_statuses),
            PedidoCompraItem.quantidade > PedidoCompraItem.quantidade_recebida,
        )
    ) or Decimal("0.00")
    pending_line_count = (
        db.scalar(
            select(func.count(PedidoCompraItem.id))
            .join(PedidoCompra, PedidoCompra.id == PedidoCompraItem.pedido_id)
            .where(
                PedidoCompra.status.in_(receiving_statuses),
                PedidoCompraItem.quantidade > PedidoCompraItem.quantidade_recebida,
            )
        )
        or 0
    )
    confirmed_receipts_in_period = (
        db.scalar(
            select(func.count(RecebimentoCompra.id)).where(
                RecebimentoCompra.status == "CONFIRMADO",
                RecebimentoCompra.data_recebimento >= date_from,
                RecebimentoCompra.data_recebimento <= date_to,
            )
        )
        or 0
    )
    received_orders_in_period = (
        db.scalar(
            select(func.count(func.distinct(RecebimentoCompra.pedido_id))).where(
                RecebimentoCompra.status == "CONFIRMADO",
                RecebimentoCompra.data_recebimento >= date_from,
                RecebimentoCompra.data_recebimento <= date_to,
            )
        )
        or 0
    )
    received_value_in_period = db.scalar(
        select(
            func.sum(
                RecebimentoCompraItem.quantidade * RecebimentoCompraItem.custo_efetivo
            )
        )
        .join(
            RecebimentoCompra,
            RecebimentoCompra.id == RecebimentoCompraItem.recebimento_id,
        )
        .where(
            RecebimentoCompra.status == "CONFIRMADO",
            RecebimentoCompra.data_recebimento >= date_from,
            RecebimentoCompra.data_recebimento <= date_to,
        )
    ) or Decimal("0.00")
    period_orders = db.scalars(
        select(PedidoCompra)
        .options(
            selectinload(PedidoCompra.fornecedor),
            selectinload(PedidoCompra.itens),
        )
        .where(
            PedidoCompra.created_at >= start_datetime,
            PedidoCompra.created_at < end_datetime,
        )
        .order_by(PedidoCompra.created_at.desc(), PedidoCompra.id.desc())
    ).all()

    order_rows = []
    for order in period_orders:
        ordered_value = sum(
            (item.quantidade * item.custo_unitario for item in order.itens),
            Decimal("0.00"),
        )
        pending_order_value = (
            sum(
                (
                    (item.quantidade - item.quantidade_recebida) * item.custo_unitario
                    for item in order.itens
                ),
                Decimal("0.00"),
            )
            if order.status in receiving_statuses
            else Decimal("0.00")
        )
        order_rows.append(
            {
                "id": order.id,
                "numero": order.numero,
                "supplier_name": order.fornecedor.nome,
                "status": order.status,
                "created_at": order.created_at.date(),
                "ordered_value": ordered_value,
                "pending_value": pending_order_value,
            }
        )

    return {
        "total_orders": total_orders,
        "pending_receipts": status_counts["EMITIDO"]
        + status_counts["PARCIALMENTE_RECEBIDO"],
        "quotes": db.scalar(select(func.count(Orcamento.id))) or 0,
        "period": period,
        "date_from": date_from,
        "date_to": date_to,
        "period_orders": period_order_count,
        "received_orders_in_period": received_orders_in_period,
        "confirmed_receipts_in_period": confirmed_receipts_in_period,
        "ordered_value_in_period": ordered_value_in_period,
        "received_value_in_period": received_value_in_period,
        "open_orders": status_counts["RASCUNHO"]
        + status_counts["EMITIDO"]
        + status_counts["PARCIALMENTE_RECEBIDO"],
        "pending_value": pending_value,
        "pending_line_count": pending_line_count,
        "status_counts": status_counts,
        "orders": order_rows,
    }


@router.get("/stock")
def stock_report(
    deposit_id: int | None = Query(default=None, gt=0),
    period: DashboardAnalyticsPeriod = Query(default="12m"),
    db: Session = Depends(get_db_session),
):
    if deposit_id is None:
        try:
            deposit_id = get_default_deposit(db).id
        except InventoryNotFound as exception:
            raise HTTPException(status_code=409, detail=str(exception)) from None
    balances = list_balances(db, deposit_id)
    deposit = db.get(DepositoEstoque, deposit_id)
    products = db.scalars(
        select(Produto).where(Produto.id.in_([item["produto_id"] for item in balances]))
    ).all()
    products_by_id = {product.id: product for product in products}
    enriched_balances = []
    for balance in balances:
        product = products_by_id[balance["produto_id"]]
        saldo = balance["saldo"]
        minimum = balance["estoque_minimo"]
        deficit = max(minimum - saldo, Decimal("0.000"))
        shortfall_percent = (
            float(deficit * 100 / minimum)
            if balance["abaixo_do_minimo"] and minimum > 0
            else None
        )
        enriched_balances.append(
            {
                **balance,
                "product_name": product.nome,
                "sku": product.sku,
                "unit": product.unidade_medida,
                "deficit": deficit,
                "shortfall_percent": shortfall_percent,
            }
        )
    date_from, date_to, granularity = _dashboard_period(period)
    movement_series = _stock_movement_trend(
        db, deposit_id, date_from, date_to, granularity
    )
    movement_entries = sum(point["entries"] for point in movement_series)
    movement_exits = sum(point["exits"] for point in movement_series)
    return {
        "balances": enriched_balances,
        "below_minimum": [
            item for item in enriched_balances if item["abaixo_do_minimo"]
        ],
        "movement_count": db.scalar(select(func.count(MovimentacaoEstoque.id))) or 0,
        "active_products": len(enriched_balances),
        "products_with_balance": sum(item["saldo"] != 0 for item in balances),
        "period": period,
        "date_from": date_from,
        "date_to": date_to,
        "granularity": granularity,
        "movement_entries": movement_entries,
        "movement_exits": movement_exits,
        "movement_count_in_period": movement_entries + movement_exits,
        "movement_series": movement_series,
        "deposit": {
            "id": deposit.id,
            "code": deposit.codigo,
            "name": deposit.nome,
        },
    }


@router.get("/finance")
def finance_report(
    period: DashboardAnalyticsPeriod = Query(default="12m"),
    db: Session = Depends(get_db_session),
):
    cashflow = cashflow_summary(db)
    date_from, date_to, granularity = _dashboard_period(period)
    return {
        **cashflow.model_dump(mode="json"),
        "period": period,
        "date_from": date_from,
        "date_to": date_to,
        "granularity": granularity,
        "commitments": _finance_commitment_trend(db, date_from, date_to, granularity),
        **_overdue_open_summary(db),
        "receivable_titles": db.scalar(
            select(func.count(TituloFinanceiro.id)).where(
                TituloFinanceiro.tipo == "RECEBER"
            )
        )
        or 0,
        "payable_titles": db.scalar(
            select(func.count(TituloFinanceiro.id)).where(
                TituloFinanceiro.tipo == "PAGAR"
            )
        )
        or 0,
        "overdue_installments": db.scalar(
            select(func.count(ParcelaFinanceira.id)).where(
                ParcelaFinanceira.vencimento < date.today()
            )
        )
        or 0,
    }


@router.get("/dashboard")
def erp_dashboard(db: Session = Depends(get_db_session)):
    cashflow = cashflow_summary(db)
    try:
        balances = list_balances(db, get_default_deposit(db).id)
    except InventoryNotFound as exception:
        raise HTTPException(status_code=409, detail=str(exception)) from None
    completed_sales = (
        db.scalar(select(func.count(Venda.id)).where(Venda.status == "CONCLUIDA")) or 0
    )
    return {
        "customers": db.scalar(select(func.count(Cliente.id))) or 0,
        "products": db.scalar(
            select(func.count(Produto.id)).where(Produto.ativo.is_(True))
        )
        or 0,
        "completed_sales": completed_sales,
        "low_stock_products": sum(item["abaixo_do_minimo"] for item in balances),
        "receivable_open": cashflow.previsto_receber,
        "payable_open": cashflow.previsto_pagar,
        "realized_receivable": cashflow.realizado_receber,
        "realized_payable": cashflow.realizado_pagar,
    }


@router.get("/dashboard/analytics", response_model=DashboardAnalyticsRead)
def dashboard_analytics(
    period: DashboardAnalyticsPeriod = Query(default="12m"),
    db: Session = Depends(get_db_session),
) -> DashboardAnalyticsRead:
    date_from, date_to, granularity = _dashboard_period(period)
    buckets = _dashboard_buckets(date_from, date_to, granularity)
    start_datetime = datetime.combine(date_from, time.min, tzinfo=timezone.utc)
    end_datetime = datetime.combine(
        date_to + timedelta(days=1), time.min, tzinfo=timezone.utc
    )

    sales_bucket = _utc_bucket(Venda.data_venda, granularity)
    sales_rows = db.execute(
        select(
            sales_bucket,
            func.coalesce(
                func.sum(VendaItem.quantidade * VendaItem.preco_unitario),
                Decimal("0.00"),
            ),
            func.count(func.distinct(Venda.id)),
        )
        .join(VendaItem, VendaItem.venda_id == Venda.id)
        .where(
            Venda.status == "CONCLUIDA",
            Venda.data_venda >= start_datetime,
            Venda.data_venda < end_datetime,
        )
        .group_by(sales_bucket)
        .order_by(sales_bucket)
    ).all()
    sales_by_bucket = {
        _bucket_date(row[0]): (row[1] or Decimal("0.00"), row[2] or 0)
        for row in sales_rows
    }

    finance_trend = _finance_commitment_trend(db, date_from, date_to, granularity)

    reverse_source = aliased(MovimentacaoEstoque)
    reverse_effect = case(
        (reverse_source.tipo.in_(POSITIVE_TYPES), -reverse_source.quantidade),
        (reverse_source.tipo.in_(NEGATIVE_TYPES), reverse_source.quantidade),
        else_=literal(Decimal("0.00")),
    )
    movement_effect = case(
        (MovimentacaoEstoque.tipo.in_(POSITIVE_TYPES), MovimentacaoEstoque.quantidade),
        (MovimentacaoEstoque.tipo.in_(NEGATIVE_TYPES), -MovimentacaoEstoque.quantidade),
        (MovimentacaoEstoque.tipo == "REVERSAO", reverse_effect),
        else_=literal(Decimal("0.00")),
    )
    try:
        deposit_id = get_default_deposit(db).id
    except InventoryNotFound as exception:
        raise HTTPException(status_code=409, detail=str(exception)) from None
    balances = (
        select(
            MovimentacaoEstoque.produto_id.label("produto_id"),
            func.sum(movement_effect).label("saldo"),
        )
        .outerjoin(
            reverse_source,
            reverse_source.id == MovimentacaoEstoque.movimento_origem_id,
        )
        .where(MovimentacaoEstoque.deposito_id == deposit_id)
        .group_by(MovimentacaoEstoque.produto_id)
        .subquery()
    )
    stock_balance = func.coalesce(balances.c.saldo, literal(Decimal("0.00")))
    shortfall_percent = case(
        (
            Produto.estoque_minimo > 0,
            (Produto.estoque_minimo - stock_balance) * 100 / Produto.estoque_minimo,
        ),
        else_=literal(Decimal("0.00")),
    )
    stock_rows = db.execute(
        select(
            Produto.id,
            Produto.nome,
            stock_balance,
            Produto.estoque_minimo,
            shortfall_percent,
        )
        .outerjoin(balances, balances.c.produto_id == Produto.id)
        .where(Produto.ativo.is_(True), stock_balance < Produto.estoque_minimo)
        .order_by(desc(shortfall_percent), Produto.id)
        .limit(5)
    ).all()

    return DashboardAnalyticsRead(
        period=period,
        date_from=date_from,
        date_to=date_to,
        granularity=granularity,
        sales_trend=[
            {
                "bucket": bucket,
                "sales_value": float(
                    sales_by_bucket.get(bucket, (Decimal("0.00"), 0))[0]
                ),
                "completed_sales": sales_by_bucket.get(bucket, (Decimal("0.00"), 0))[1],
            }
            for bucket in buckets
        ],
        finance_trend=finance_trend,
        stock_attention=[
            {
                "product_id": row[0],
                "product_name": row[1],
                "saldo": float(row[2] or Decimal("0.00")),
                "estoque_minimo": float(row[3] or Decimal("0.00")),
                "shortfall_percent": float(row[4] or Decimal("0.00")),
            }
            for row in stock_rows
        ],
    )
