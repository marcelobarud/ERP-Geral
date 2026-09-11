from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import Field

from app.schemas.base import APIModel, ReadModel

MovementType = Literal[
    "ENTRADA",
    "SAIDA",
    "AJUSTE_ENTRADA",
    "AJUSTE_SAIDA",
    "DEVOLUCAO_ENTRADA",
    "DEVOLUCAO_SAIDA",
    "REVERSAO",
]
InventoryStatus = Literal["RASCUNHO", "CONFIRMADO", "CANCELADO"]


class DepositCreate(APIModel):
    codigo: str = Field(min_length=1, max_length=40)
    nome: str = Field(min_length=1, max_length=100)
    padrao: bool = False


class DepositUpdate(APIModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=40)
    nome: str | None = Field(default=None, min_length=1, max_length=100)
    ativo: bool | None = None
    padrao: bool | None = None


class DepositRead(ReadModel):
    id: int
    codigo: str
    nome: str
    ativo: bool
    padrao: bool
    created_at: datetime
    updated_at: datetime


class InventoryConfigUpdate(APIModel):
    permitir_saldo_negativo: bool


class InventoryConfigRead(ReadModel):
    id: int
    permitir_saldo_negativo: bool
    updated_at: datetime


class StockMovementCreate(APIModel):
    produto_id: int = Field(gt=0)
    deposito_id: int = Field(gt=0)
    tipo: MovementType
    quantidade: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    data_movimentacao: datetime
    origem: str = Field(min_length=1, max_length=40)
    documento_tipo: str | None = Field(default=None, max_length=40)
    documento_id: int | None = Field(default=None, gt=0)
    movimento_origem_id: int | None = Field(default=None, gt=0)
    observacao: str | None = Field(default=None, max_length=500)
    chave_idempotencia: str | None = Field(default=None, min_length=1, max_length=120)


class StockMovementRead(ReadModel):
    id: int
    produto_id: int
    deposito_id: int
    tipo: MovementType
    quantidade: Decimal
    data_movimentacao: datetime
    origem: str
    documento_tipo: str | None
    documento_id: int | None
    movimento_origem_id: int | None
    usuario_id: int | None
    observacao: str | None
    chave_idempotencia: str | None
    created_at: datetime


class StockBalanceRead(ReadModel):
    produto_id: int
    deposito_id: int
    saldo: Decimal
    estoque_minimo: Decimal
    abaixo_do_minimo: bool


class InventoryItemCreate(APIModel):
    produto_id: int = Field(gt=0)
    quantidade_contada: Decimal = Field(
        ge=0, max_digits=12, decimal_places=3
    )


class InventoryItemRead(ReadModel):
    id: int
    produto_id: int
    saldo_sistema: Decimal
    quantidade_contada: Decimal
    diferenca: Decimal


class InventoryCreate(APIModel):
    deposito_id: int = Field(gt=0)
    data_inventario: date
    observacao: str | None = Field(default=None, max_length=500)
    itens: list[InventoryItemCreate] = Field(min_length=1)


class InventoryRead(ReadModel):
    id: int
    deposito_id: int
    data_inventario: date
    status: InventoryStatus
    usuario_id: int | None
    observacao: str | None
    created_at: datetime
    updated_at: datetime
    itens: list[InventoryItemRead]
