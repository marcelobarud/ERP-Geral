from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.base import APIModel, ReadModel


class CategoriaProdutoCreate(APIModel):
    nome: str = Field(min_length=1, max_length=100)


class CategoriaProdutoRead(ReadModel):
    id: int
    nome: str
    ativo: bool
    created_at: datetime
    updated_at: datetime


class UnidadeMedidaRead(ReadModel):
    id: int
    codigo: str
    nome: str
    ativo: bool


class ProdutoFornecedorCreate(APIModel):
    fornecedor_id: int = Field(gt=0)
    codigo_fornecedor: str | None = Field(default=None, max_length=80)
    custo_referencia: Decimal | None = Field(
        default=None, ge=0, max_digits=12, decimal_places=2
    )
    preferencial: bool = False
    ativo: bool = True


class ProdutoFornecedorRead(ReadModel):
    id: int
    produto_id: int
    fornecedor_id: int
    codigo_fornecedor: str | None
    custo_referencia: Decimal | None
    preferencial: bool
    ativo: bool
    created_at: datetime
    updated_at: datetime
