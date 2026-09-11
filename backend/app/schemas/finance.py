from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import Field

from app.schemas.base import APIModel, ReadModel

FinancialType = Literal["RECEBER", "PAGAR"]
FinancialStatus = Literal["ABERTO", "PARCIAL", "PAGO", "VENCIDO", "CANCELADO"]


class FinancialCategoryCreate(APIModel):
    nome: str = Field(min_length=1, max_length=100)
    tipo: FinancialType


class FinancialCategoryRead(ReadModel):
    id: int
    nome: str
    tipo: FinancialType
    ativo: bool


class FinancialAccountCreate(APIModel):
    nome: str = Field(min_length=1, max_length=100)
    saldo_inicial: Decimal = Field(
        default=Decimal("0"), max_digits=12, decimal_places=2
    )


class FinancialAccountRead(ReadModel):
    id: int
    nome: str
    saldo_inicial: Decimal
    ativo: bool


class FinancialTitleCreate(APIModel):
    numero: str | None = Field(default=None, max_length=60)
    cliente_id: int | None = Field(default=None, gt=0)
    fornecedor_id: int | None = Field(default=None, gt=0)
    categoria_id: int | None = Field(default=None, gt=0)
    origem_tipo: str | None = Field(default=None, max_length=40)
    origem_id: int | None = Field(default=None, gt=0)
    valor_original: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    descricao: str | None = Field(default=None, max_length=255)
    vencimentos: list[date] = Field(min_length=1)


class FinancialSettlementCreate(APIModel):
    conta_id: int = Field(gt=0)
    valor: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    data_liquidacao: date
    observacao: str | None = Field(default=None, max_length=255)


class FinancialSettlementRead(ReadModel):
    id: int
    parcela_id: int
    conta_id: int
    valor: Decimal
    data_liquidacao: date
    status: Literal["CONFIRMADA", "ESTORNADA"]
    observacao: str | None
    created_at: datetime


class FinancialInstallmentRead(ReadModel):
    id: int
    numero: int
    vencimento: date
    valor: Decimal
    valor_liquidado: Decimal
    status: FinancialStatus


class FinancialTitleRead(ReadModel):
    id: int
    numero: str
    tipo: FinancialType
    cliente_id: int | None
    fornecedor_id: int | None
    categoria_id: int | None
    origem_tipo: str | None
    origem_id: int | None
    valor_original: Decimal
    valor_liquidado: Decimal
    saldo: Decimal
    status: FinancialStatus
    descricao: str | None
    created_at: datetime
    updated_at: datetime
    parcelas: list[FinancialInstallmentRead]


class CashflowRead(ReadModel):
    previsto_receber: Decimal
    previsto_pagar: Decimal
    realizado_receber: Decimal
    realizado_pagar: Decimal
