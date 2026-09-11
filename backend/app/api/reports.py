from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import require_authenticated
from app.db.session import get_db_session
from app.models import (
    Cliente,
    DevolucaoVenda,
    MovimentacaoEstoque,
    Orcamento,
    ParcelaFinanceira,
    PedidoCompra,
    Produto,
    TituloFinanceiro,
    Venda,
    VendaItem,
)
from app.services.finance import cashflow_summary
from app.services.inventory import list_balances

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


@router.get("/commercial")
def commercial_report(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db_session),
):
    sales_query = date_filters(select(Venda), Venda.data_venda, date_from, date_to)
    sales = db.scalars(sales_query).all()
    by_customer = db.execute(
        date_filters(
            select(
                Venda.cliente_id,
                func.count(Venda.id),
                func.sum(VendaItem.quantidade * VendaItem.preco_unitario),
            )
            .join(VendaItem, VendaItem.venda_id == Venda.id)
            .where(Venda.status == "CONCLUIDA")
            .group_by(Venda.cliente_id),
            Venda.data_venda,
            date_from,
            date_to,
        )
    ).all()
    by_product = db.execute(
        date_filters(
            select(
                VendaItem.produto_id,
                func.sum(VendaItem.quantidade),
                func.sum(VendaItem.quantidade * VendaItem.preco_unitario),
            )
            .join(Venda, Venda.id == VendaItem.venda_id)
            .where(Venda.status == "CONCLUIDA")
            .group_by(VendaItem.produto_id),
            Venda.data_venda,
            date_from,
            date_to,
        )
    ).all()
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
        "by_customer": [
            {"customer_id": row[0], "sales": row[1], "total": row[2] or Decimal("0")}
            for row in by_customer
        ],
        "by_product": [
            {
                "product_id": row[0],
                "quantity": row[1] or Decimal("0"),
                "total": row[2] or Decimal("0"),
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
    deposit_id: int = Query(default=1, gt=0),
    db: Session = Depends(get_db_session),
):
    balances = list_balances(db, deposit_id)
    return {
        "balances": balances,
        "below_minimum": [item for item in balances if item["abaixo_do_minimo"]],
        "movement_count": db.scalar(select(func.count(MovimentacaoEstoque.id))) or 0,
    }


@router.get("/finance")
def finance_report(db: Session = Depends(get_db_session)):
    cashflow = cashflow_summary(db)
    return {
        **cashflow.model_dump(mode="json"),
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
    balances = list_balances(db, 1)
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
