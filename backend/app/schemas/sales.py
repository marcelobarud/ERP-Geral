from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import Field, model_validator

from app.schemas.base import APIModel, ReadModel

VendaStatus = Literal["CONCLUIDA", "CANCELADA"]


class VendaItemCreate(APIModel):
    produto_id: int = Field(gt=0)
    quantidade: Decimal = Field(gt=0, max_digits=12, decimal_places=3)


class VendaCreate(APIModel):
    cliente_id: int = Field(gt=0)
    funcionario_id: int = Field(gt=0)
    data_venda: datetime
    condicao_pagamento_id: int | None = Field(default=None, gt=0)
    observacao: str | None = Field(default=None, max_length=1000)
    itens: list[VendaItemCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def reject_repeated_products(self) -> "VendaCreate":
        product_ids = [item.produto_id for item in self.itens]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("O mesmo produto não pode aparecer mais de uma vez.")
        return self


class VendaCancel(APIModel):
    motivo: str | None = Field(default=None, max_length=500)


class ClienteResumo(ReadModel):
    id: int
    nome: str


class FuncionarioResumo(ReadModel):
    id: int
    nome_completo: str


class ProdutoResumo(ReadModel):
    id: int
    nome: str


class FornecedorResumo(ReadModel):
    id: int
    nome: str


class VendaItemRead(ReadModel):
    id: int
    produto: ProdutoResumo
    fornecedor_id: int
    fornecedor: FornecedorResumo
    quantidade: Decimal
    preco_unitario: Decimal
    subtotal: Decimal
    created_at: datetime
    updated_at: datetime


class VendaRead(ReadModel):
    id: int
    data_venda: datetime
    status: VendaStatus
    cancelada_em: datetime | None
    motivo_cancelamento: str | None
    pedido_id: int | None
    condicao_pagamento_id: int | None
    observacao: str | None
    created_at: datetime
    updated_at: datetime
    cliente: ClienteResumo
    funcionario: FuncionarioResumo
    itens: list[VendaItemRead]
    total: Decimal
