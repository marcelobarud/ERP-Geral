from datetime import date, datetime

from pydantic import Field, model_validator

from app.schemas.base import APIModel, ReadModel
from app.schemas.custom_fields import CustomFieldValueRead


class FuncionarioCreate(APIModel):
    nome_completo: str = Field(min_length=1, max_length=255)
    cidade: str = Field(min_length=1, max_length=100)
    estado: str = Field(min_length=2, max_length=2)
    rua: str = Field(min_length=1, max_length=255)
    numero: str = Field(min_length=1, max_length=20)
    complemento: str | None = Field(default=None, max_length=255)
    cpf: str = Field(min_length=1, max_length=14)
    rg: str | None = Field(default=None, max_length=20)
    data_nascimento: date
    campos_personalizados: dict[str, object] = Field(default_factory=dict)


class FuncionarioUpdate(APIModel):
    nome_completo: str | None = Field(default=None, min_length=1, max_length=255)
    cidade: str | None = Field(default=None, min_length=1, max_length=100)
    estado: str | None = Field(default=None, min_length=2, max_length=2)
    rua: str | None = Field(default=None, min_length=1, max_length=255)
    numero: str | None = Field(default=None, min_length=1, max_length=20)
    complemento: str | None = Field(default=None, max_length=255)
    cpf: str | None = Field(default=None, min_length=1, max_length=14)
    rg: str | None = Field(default=None, max_length=20)
    data_nascimento: date | None = None
    ativo: bool | None = None
    campos_personalizados: dict[str, object] | None = None

    @model_validator(mode="after")
    def reject_null_required_fields(self) -> "FuncionarioUpdate":
        required_fields = (
            "nome_completo",
            "cidade",
            "estado",
            "rua",
            "numero",
            "cpf",
            "data_nascimento",
            "ativo",
        )
        for field_name in required_fields:
            if (
                field_name in self.model_fields_set
                and getattr(self, field_name) is None
            ):
                raise ValueError(f"{field_name} não pode ser nulo.")
        return self


class FuncionarioRead(ReadModel):
    id: int
    nome_completo: str
    cidade: str
    estado: str
    rua: str
    numero: str
    complemento: str | None = None
    cpf: str
    rg: str | None = None
    data_nascimento: date
    ativo: bool
    created_at: datetime
    updated_at: datetime
    campos_personalizados: list[CustomFieldValueRead] = Field(default_factory=list)
