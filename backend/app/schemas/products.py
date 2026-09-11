from datetime import datetime
from decimal import Decimal

from pydantic import Field, model_validator

from app.schemas.base import APIModel, ReadModel
from app.schemas.custom_fields import CustomFieldValueRead


class ProdutoCreate(APIModel):
    nome: str = Field(min_length=1, max_length=255)
    sku: str | None = Field(default=None, min_length=1, max_length=80)
    codigo_barras: str | None = Field(default=None, min_length=1, max_length=80)
    categoria: str = Field(min_length=1, max_length=100)
    categoria_id: int | None = Field(default=None, gt=0)
    unidade_medida: str = Field(default="UN", min_length=1, max_length=10)
    ativo: bool = True
    estoque_minimo: Decimal = Field(
        default=Decimal("0"), ge=0, max_digits=12, decimal_places=3
    )
    preco_custo: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    preco_venda: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    fornecedor_id: int = Field(gt=0)
    campos_personalizados: dict[str, object] = Field(default_factory=dict)


class ProdutoUpdate(APIModel):
    nome: str | None = Field(default=None, min_length=1, max_length=255)
    sku: str | None = Field(default=None, min_length=1, max_length=80)
    codigo_barras: str | None = Field(default=None, min_length=1, max_length=80)
    categoria: str | None = Field(default=None, min_length=1, max_length=100)
    categoria_id: int | None = Field(default=None, gt=0)
    unidade_medida: str | None = Field(default=None, min_length=1, max_length=10)
    ativo: bool | None = None
    estoque_minimo: Decimal | None = Field(
        default=None, ge=0, max_digits=12, decimal_places=3
    )
    preco_custo: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
    )
    preco_venda: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
    )
    fornecedor_id: int | None = Field(default=None, gt=0)
    campos_personalizados: dict[str, object] | None = None

    @model_validator(mode="after")
    def reject_null_required_fields(self) -> "ProdutoUpdate":
        required_fields = (
            "nome",
            "sku",
            "categoria",
            "preco_custo",
            "preco_venda",
            "fornecedor_id",
        )
        for field_name in required_fields:
            if (
                field_name in self.model_fields_set
                and getattr(self, field_name) is None
            ):
                raise ValueError(f"{field_name} não pode ser nulo.")
        return self


class ProdutoRead(ReadModel):
    id: int
    nome: str
    sku: str
    codigo_barras: str | None
    categoria: str
    categoria_id: int | None
    unidade_medida: str
    ativo: bool
    estoque_minimo: Decimal
    preco_custo: Decimal
    preco_venda: Decimal
    fornecedor_id: int
    created_at: datetime
    updated_at: datetime
    campos_personalizados: list[CustomFieldValueRead] = Field(default_factory=list)
