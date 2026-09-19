from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, desc, func, literal, select
from sqlalchemy.orm import Session, aliased

from app.api.dependencies import require_authenticated
from app.db.session import get_db_session
from app.models import (
    Cliente,
    DevolucaoVenda,
    LiquidacaoFinanceira,
    MovimentacaoEstoque,
    Orcamento,
    ParcelaFinanceira,
    PedidoCompra,
    Produto,
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
        sales_bucket = func.date_trunc(granularity, Venda.data_venda)
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
def purchases_report(db: Session = Depends(get_db_session)):
    pending = (
        db.scalar(
            select(func.count(PedidoCompra.id)).where(
                PedidoCompra.status.in_(["EMITIDO", "PARCIALMENTE_RECEBIDO"])
            )
        )
        or 0
    )
    return {
        "total_orders": db.scalar(select(func.count(PedidoCompra.id))) or 0,
        "pending_receipts": pending,
        "quotes": db.scalar(select(func.count(Orcamento.id))) or 0,
    }


@router.get("/stock")
def stock_report(
    deposit_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db_session),
):
    if deposit_id is None:
        try:
            deposit_id = get_default_deposit(db).id
        except InventoryNotFound as exception:
            raise HTTPException(status_code=409, detail=str(exception)) from None
    balances = list_balances(db, deposit_id)
    return {
        "balances": balances,
        "below_minimum": [item for item in balances if item["abaixo_do_minimo"]],
        "movement_count": db.scalar(select(func.count(MovimentacaoEstoque.id))) or 0,
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

    sales_bucket = func.date_trunc(granularity, Venda.data_venda)
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
