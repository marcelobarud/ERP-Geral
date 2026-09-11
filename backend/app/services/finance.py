"""Regras do financeiro operacional sem contabilidade formal."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    CategoriaFinanceira,
    Cliente,
    ContaFinanceira,
    Fornecedor,
    LiquidacaoFinanceira,
    ParcelaFinanceira,
    TituloFinanceiro,
)
from app.schemas.finance import FinancialTitleCreate


class FinanceNotFound(Exception):
    pass


class FinanceConflict(Exception):
    pass


def title_query():
    return select(TituloFinanceiro).options(
        selectinload(TituloFinanceiro.parcelas).selectinload(
            ParcelaFinanceira.liquidacoes
        )
    )


def get_title(db: Session, title_id: int) -> TituloFinanceiro | None:
    return db.scalar(title_query().where(TituloFinanceiro.id == title_id))


def settlement_total(installment: ParcelaFinanceira) -> Decimal:
    return sum(
        (item.valor for item in installment.liquidacoes if item.status == "CONFIRMADA"),
        Decimal("0.00"),
    )


def installment_status(installment: ParcelaFinanceira, today: date) -> str:
    settled = settlement_total(installment)
    if settled >= installment.valor:
        return "PAGO"
    if settled > 0:
        return "PARCIAL"
    if installment.vencimento < today:
        return "VENCIDO"
    return "ABERTO"


def title_status(title: TituloFinanceiro, today: date | None = None) -> str:
    current_date = today or date.today()
    statuses = [installment_status(item, current_date) for item in title.parcelas]
    if statuses and all(item == "PAGO" for item in statuses):
        return "PAGO"
    if any(item == "PARCIAL" for item in statuses):
        return "PARCIAL"
    if any(item == "VENCIDO" for item in statuses):
        return "VENCIDO"
    return "ABERTO"


def create_title(
    db: Session, title_type: str, payload: FinancialTitleCreate
) -> TituloFinanceiro:
    if title_type == "RECEBER":
        if payload.cliente_id is None:
            raise FinanceConflict("Título a receber exige cliente.")
        if db.get(Cliente, payload.cliente_id) is None:
            raise FinanceNotFound("Cliente não encontrado.")
    if title_type == "PAGAR":
        if payload.fornecedor_id is None:
            raise FinanceConflict("Título a pagar exige fornecedor.")
        if db.get(Fornecedor, payload.fornecedor_id) is None:
            raise FinanceNotFound("Fornecedor não encontrado.")
    if (
        payload.categoria_id
        and db.get(CategoriaFinanceira, payload.categoria_id) is None
    ):
        raise FinanceNotFound("Categoria financeira não encontrada.")
    if len(payload.vencimentos) > 1:
        expected = sum(
            (payload.valor_original / len(payload.vencimentos),)
            * len(payload.vencimentos),
            Decimal("0"),
        )
        values = [expected.quantize(Decimal("0.01"))] * len(payload.vencimentos)
        values[-1] += payload.valor_original - sum(values)
    else:
        values = [payload.valor_original]
    if sum(values, Decimal("0")) != payload.valor_original:
        raise FinanceConflict("O parcelamento não fecha o valor original.")
    title = TituloFinanceiro(
        numero=payload.numero or f"FIN-{uuid4().hex[:12].upper()}",
        tipo=title_type,
        cliente_id=payload.cliente_id,
        fornecedor_id=payload.fornecedor_id,
        categoria_id=payload.categoria_id,
        origem_tipo=payload.origem_tipo,
        origem_id=payload.origem_id,
        valor_original=payload.valor_original,
        descricao=payload.descricao,
        parcelas=[
            ParcelaFinanceira(numero=index, vencimento=due, valor=value)
            for index, (due, value) in enumerate(zip(payload.vencimentos, values), 1)
        ],
    )
    db.add(title)
    db.commit()
    return get_title(db, title.id)  # type: ignore[return-value]


def settle_installment(
    db: Session,
    installment_id: int,
    account_id: int,
    value: Decimal,
    data: date,
    observation: str | None,
) -> LiquidacaoFinanceira:
    installment = db.get(ParcelaFinanceira, installment_id)
    if installment is None:
        raise FinanceNotFound("Parcela não encontrada.")
    account = db.get(ContaFinanceira, account_id)
    if account is None or not account.ativo:
        raise FinanceNotFound("Conta financeira não encontrada.")
    remaining = installment.valor - settlement_total(
        db.scalar(
            select(ParcelaFinanceira)
            .options(selectinload(ParcelaFinanceira.liquidacoes))
            .where(ParcelaFinanceira.id == installment.id)
        )
    )
    if value > remaining:
        raise FinanceConflict("Liquidação maior que o saldo da parcela.")
    settlement = LiquidacaoFinanceira(
        parcela_id=installment.id,
        conta_id=account.id,
        valor=value,
        data_liquidacao=data,
        observacao=observation,
    )
    db.add(settlement)
    db.commit()
    db.refresh(settlement)
    return settlement


def reverse_settlement(db: Session, settlement_id: int) -> LiquidacaoFinanceira:
    settlement = db.get(LiquidacaoFinanceira, settlement_id)
    if settlement is None:
        raise FinanceNotFound("Liquidação não encontrada.")
    if settlement.status == "ESTORNADA":
        return settlement
    settlement.status = "ESTORNADA"
    db.commit()
    db.refresh(settlement)
    return settlement


def title_to_read(title: TituloFinanceiro):
    from app.schemas.finance import FinancialInstallmentRead, FinancialTitleRead

    liquidated = sum(
        (settlement_total(item) for item in title.parcelas), Decimal("0.00")
    )
    return FinancialTitleRead(
        id=title.id,
        numero=title.numero,
        tipo=title.tipo,
        cliente_id=title.cliente_id,
        fornecedor_id=title.fornecedor_id,
        categoria_id=title.categoria_id,
        origem_tipo=title.origem_tipo,
        origem_id=title.origem_id,
        valor_original=title.valor_original,
        valor_liquidado=liquidated,
        saldo=title.valor_original - liquidated,
        status=title_status(title),
        descricao=title.descricao,
        created_at=title.created_at,
        updated_at=title.updated_at,
        parcelas=[
            FinancialInstallmentRead(
                id=item.id,
                numero=item.numero,
                vencimento=item.vencimento,
                valor=item.valor,
                valor_liquidado=settlement_total(item),
                status=installment_status(item, date.today()),
            )
            for item in title.parcelas
        ],
    )


def cashflow_summary(db: Session):
    titles = db.scalars(title_query()).all()
    previsto_receber = sum(
        (
            title.valor_original
            - sum((settlement_total(item) for item in title.parcelas), Decimal("0"))
            for title in titles
            if title.tipo == "RECEBER"
        ),
        Decimal("0.00"),
    )
    previsto_pagar = sum(
        (
            title.valor_original
            - sum((settlement_total(item) for item in title.parcelas), Decimal("0"))
            for title in titles
            if title.tipo == "PAGAR"
        ),
        Decimal("0.00"),
    )
    realized = db.scalars(
        select(LiquidacaoFinanceira).where(LiquidacaoFinanceira.status == "CONFIRMADA")
    ).all()
    realized_receber = Decimal("0.00")
    realized_pagar = Decimal("0.00")
    for settlement in realized:
        title = settlement.parcela.titulo
        if title.tipo == "RECEBER":
            realized_receber += settlement.valor
        else:
            realized_pagar += settlement.valor
    from app.schemas.finance import CashflowRead

    return CashflowRead(
        previsto_receber=previsto_receber,
        previsto_pagar=previsto_pagar,
        realizado_receber=realized_receber,
        realizado_pagar=realized_pagar,
    )
