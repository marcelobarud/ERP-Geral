from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import Field

from app.schemas.base import APIModel, ReadModel

ReturnStatus = Literal["RASCUNHO", "APROVADA", "CANCELADA"]


class ReturnItemCreate(APIModel):
    venda_item_id: int = Field(gt=0)
    quantidade: Decimal = Field(gt=0, max_digits=12, decimal_places=3)


class ReturnCreate(APIModel):
    motivo: str = Field(min_length=1, max_length=500)
    itens: list[ReturnItemCreate] = Field(min_length=1)


class ReturnItemRead(ReadModel):
    id: int
    venda_item_id: int
    produto_id: int
    produto_nome: str
    quantidade: Decimal
    preco_unitario: Decimal


class ReturnRead(ReadModel):
    id: int
    venda_id: int
    status: ReturnStatus
    motivo: str
    usuario_id: int | None
    created_at: datetime
    updated_at: datetime
    itens: list[ReturnItemRead]
