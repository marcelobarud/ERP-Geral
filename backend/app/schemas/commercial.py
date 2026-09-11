from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import Field

from app.schemas.base import APIModel, ReadModel

QuoteStatus = Literal[
    "RASCUNHO",
    "ENVIADO",
    "APROVADO",
    "RECUSADO",
    "EXPIRADO",
    "CANCELADO",
]
OrderStatus = Literal["RASCUNHO", "CONFIRMADO", "CONCLUIDO", "CANCELADO"]


class PaymentConditionCreate(APIModel):
    codigo: str = Field(min_length=1, max_length=40)
    nome: str = Field(min_length=1, max_length=100)
    descricao: str | None = Field(default=None, max_length=255)


class PaymentConditionRead(ReadModel):
    id: int
    codigo: str
    nome: str
    descricao: str | None
    ativo: bool


class CommercialItemCreate(APIModel):
    produto_id: int = Field(gt=0)
    quantidade: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    preco_unitario: Decimal | None = Field(
        default=None, ge=0, max_digits=12, decimal_places=2
    )
    desconto: Decimal = Field(
        default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2
    )
    acrescimo: Decimal = Field(
        default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2
    )


class CommercialItemRead(ReadModel):
    id: int
    produto_id: int
    produto_nome: str
    sku: str
    fornecedor_id: int
    fornecedor_nome: str
    quantidade: Decimal
    preco_unitario: Decimal
    desconto: Decimal
    acrescimo: Decimal
    total: Decimal


class QuoteCreate(APIModel):
    numero: str | None = Field(default=None, min_length=1, max_length=40)
    cliente_id: int = Field(gt=0)
    funcionario_id: int | None = Field(default=None, gt=0)
    condicao_pagamento_id: int | None = Field(default=None, gt=0)
    validade: date | None = None
    desconto: Decimal = Field(
        default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2
    )
    acrescimo: Decimal = Field(
        default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2
    )
    frete: Decimal = Field(
        default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2
    )
    observacao: str | None = Field(default=None, max_length=1000)
    itens: list[CommercialItemCreate] = Field(min_length=1)


class QuoteStatusUpdate(APIModel):
    status: QuoteStatus


class QuoteRead(ReadModel):
    id: int
    numero: str
    cliente_id: int
    funcionario_id: int | None
    condicao_pagamento_id: int | None
    validade: date | None
    desconto: Decimal
    acrescimo: Decimal
    frete: Decimal
    status: QuoteStatus
    observacao: str | None
    created_at: datetime
    updated_at: datetime
    itens: list[CommercialItemRead]
    subtotal: Decimal
    total: Decimal
    pedido_id: int | None


class OrderCreate(APIModel):
    numero: str | None = Field(default=None, min_length=1, max_length=40)
    cliente_id: int = Field(gt=0)
    funcionario_id: int | None = Field(default=None, gt=0)
    orcamento_id: int | None = Field(default=None, gt=0)
    condicao_pagamento_id: int | None = Field(default=None, gt=0)
    desconto: Decimal = Field(
        default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2
    )
    acrescimo: Decimal = Field(
        default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2
    )
    frete: Decimal = Field(
        default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2
    )
    observacao: str | None = Field(default=None, max_length=1000)
    itens: list[CommercialItemCreate] = Field(min_length=1)


class OrderStatusUpdate(APIModel):
    status: OrderStatus


class OrderRead(ReadModel):
    id: int
    numero: str
    cliente_id: int
    funcionario_id: int | None
    orcamento_id: int | None
    venda_id: int | None
    condicao_pagamento_id: int | None
    desconto: Decimal
    acrescimo: Decimal
    frete: Decimal
    status: OrderStatus
    observacao: str | None
    created_at: datetime
    updated_at: datetime
    itens: list[CommercialItemRead]
    subtotal: Decimal
    total: Decimal
