from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import Field

from app.schemas.base import APIModel, ReadModel

PurchaseStatus = Literal[
    "RASCUNHO", "EMITIDO", "PARCIALMENTE_RECEBIDO", "RECEBIDO", "CANCELADO"
]
ReceiptStatus = Literal["RASCUNHO", "CONFIRMADO", "CANCELADO"]


class PurchaseItemCreate(APIModel):
    produto_id: int = Field(gt=0)
    quantidade: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    custo_unitario: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class PurchaseCreate(APIModel):
    numero: str | None = Field(default=None, min_length=1, max_length=40)
    fornecedor_id: int = Field(gt=0)
    previsao_entrega: date | None = None
    observacao: str | None = Field(default=None, max_length=1000)
    itens: list[PurchaseItemCreate] = Field(min_length=1)


class PurchaseStatusUpdate(APIModel):
    status: PurchaseStatus


class PurchaseUpdate(APIModel):
    numero: str | None = Field(default=None, min_length=1, max_length=40)
    fornecedor_id: int | None = Field(default=None, gt=0)
    previsao_entrega: date | None = None
    observacao: str | None = Field(default=None, max_length=1000)
    itens: list[PurchaseItemCreate] | None = Field(default=None, min_length=1)


class PurchaseItemRead(ReadModel):
    id: int
    produto_id: int
    produto_nome: str
    sku: str
    quantidade: Decimal
    quantidade_recebida: Decimal
    pendente: Decimal
    custo_unitario: Decimal


class PurchaseRead(ReadModel):
    id: int
    numero: str
    fornecedor_id: int
    status: PurchaseStatus
    previsao_entrega: date | None
    observacao: str | None
    created_at: datetime
    updated_at: datetime
    itens: list[PurchaseItemRead]


class ReceiptItemCreate(APIModel):
    pedido_item_id: int = Field(gt=0)
    quantidade: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    custo_efetivo: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class ReceiptCreate(APIModel):
    data_recebimento: date
    observacao: str | None = Field(default=None, max_length=500)
    itens: list[ReceiptItemCreate] = Field(min_length=1)


class ReceiptRead(ReadModel):
    id: int
    pedido_id: int
    data_recebimento: date
    status: ReceiptStatus
    usuario_id: int | None
    observacao: str | None
    created_at: datetime
    updated_at: datetime
    itens: list["ReceiptItemRead"]


class ReceiptItemRead(ReadModel):
    id: int
    pedido_item_id: int
    produto_id: int
    quantidade: Decimal
    custo_efetivo: Decimal
