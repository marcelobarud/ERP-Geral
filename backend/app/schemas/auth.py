from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator

from app.schemas.base import APIModel, ReadModel

UserRole = Literal["ADMIN", "MANAGER", "OPERATOR"]


def normalize_email(value: str) -> str:
    normalized = value.strip().lower()
    if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
        raise ValueError("Informe um e-mail válido.")
    return normalized


class LoginRequest(APIModel):
    email: str = Field(min_length=3, max_length=320)
    senha: str = Field(min_length=12, max_length=128)

    _normalize_email = field_validator("email")(normalize_email)


class BootstrapRequest(LoginRequest):
    nome: str = Field(min_length=2, max_length=255)
    token: str | None = Field(default=None, min_length=16, max_length=255)


class UsuarioCreate(APIModel):
    nome: str = Field(min_length=2, max_length=255)
    email: str = Field(min_length=3, max_length=320)
    senha: str = Field(min_length=12, max_length=128)
    role: UserRole = "OPERATOR"
    funcionario_id: int | None = Field(default=None, gt=0)

    _normalize_email = field_validator("email")(normalize_email)


class UsuarioUpdate(APIModel):
    nome: str | None = Field(default=None, min_length=2, max_length=255)
    email: str | None = Field(default=None, min_length=3, max_length=320)
    senha: str | None = Field(default=None, min_length=12, max_length=128)
    role: UserRole | None = None
    ativo: bool | None = None
    funcionario_id: int | None = Field(default=None, gt=0)

    _normalize_email = field_validator("email")(normalize_email)


class UsuarioRead(ReadModel):
    id: int
    nome: str
    email: str
    ativo: bool
    role: UserRole
    funcionario_id: int | None
    created_at: datetime
    updated_at: datetime


class LoginResponse(APIModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: datetime
    usuario: UsuarioRead


class AuthConfigRead(APIModel):
    auth_required: bool


class AuditLogRead(ReadModel):
    id: int
    usuario_id: int | None
    acao: str
    entidade: str
    entidade_id: int | None
    metadata_json: dict | None
    created_at: datetime

    @field_validator("metadata_json", mode="before")
    @classmethod
    def normalize_metadata(cls, value: object) -> dict | None:
        return value if isinstance(value, dict) else None
