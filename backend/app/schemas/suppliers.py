from datetime import datetime

from pydantic import Field, model_validator

from app.schemas.base import APIModel, ReadModel
from app.schemas.custom_fields import CustomFieldValueRead


class FornecedorCreate(APIModel):
    nome: str = Field(min_length=1, max_length=255)
    cidade: str = Field(min_length=1, max_length=100)
    estado: str = Field(min_length=2, max_length=2)
    rua: str = Field(min_length=1, max_length=255)
    numero: str = Field(min_length=1, max_length=20)
    complemento: str | None = Field(default=None, max_length=255)
    cnpj: str = Field(min_length=1, max_length=18)
    campos_personalizados: dict[str, object] = Field(default_factory=dict)


class FornecedorUpdate(APIModel):
    nome: str | None = Field(default=None, min_length=1, max_length=255)
    cidade: str | None = Field(default=None, min_length=1, max_length=100)
    estado: str | None = Field(default=None, min_length=2, max_length=2)
    rua: str | None = Field(default=None, min_length=1, max_length=255)
    numero: str | None = Field(default=None, min_length=1, max_length=20)
    complemento: str | None = Field(default=None, max_length=255)
    cnpj: str | None = Field(default=None, min_length=1, max_length=18)
    campos_personalizados: dict[str, object] | None = None

    @model_validator(mode="after")
    def reject_null_required_fields(self) -> "FornecedorUpdate":
        required_fields = ("nome", "cidade", "estado", "rua", "numero", "cnpj")
        for field_name in required_fields:
            if (
                field_name in self.model_fields_set
                and getattr(self, field_name) is None
            ):
                raise ValueError(f"{field_name} não pode ser nulo.")
        return self


class FornecedorRead(ReadModel):
    id: int
    nome: str
    cidade: str
    estado: str
    rua: str
    numero: str
    complemento: str | None = None
    cnpj: str
    created_at: datetime
    updated_at: datetime
    campos_personalizados: list[CustomFieldValueRead] = Field(default_factory=list)


class FornecedorProdutoRead(ReadModel):
    id: int
    nome: str


class FornecedorDetailRead(FornecedorRead):
    produtos: list[FornecedorProdutoRead] = Field(default_factory=list)
