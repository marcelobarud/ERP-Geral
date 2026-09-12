from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    database_url: str = Field(description="URL de conexão do PostgreSQL")
    app_name: str = "ERP Geral"
    environment: str = "development"
    auth_required: bool = False
    auth_secret: str | None = None
    auth_token_expiration_minutes: int = Field(default=60, ge=5, le=1440)
    auth_bootstrap_token: str | None = None

    model_config = SettingsConfigDict(
        # O .env oficial fica na raiz do monorepo, independentemente do CWD.
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        normalized_value = value.strip()
        if not normalized_value.startswith("postgresql+psycopg://"):
            raise ValueError(
                "DATABASE_URL deve usar o driver PostgreSQL postgresql+psycopg"
            )
        return normalized_value

    @model_validator(mode="after")
    def validate_authentication_settings(self) -> "Settings":
        is_production = self.environment.strip().lower() == "production"
        if is_production:
            self.auth_required = True
            if not self.auth_secret or len(self.auth_secret) < 32:
                raise ValueError(
                    "AUTH_SECRET deve possuir pelo menos 32 caracteres em produção"
                )
            if not self.auth_bootstrap_token or len(self.auth_bootstrap_token) < 16:
                raise ValueError(
                    "AUTH_BOOTSTRAP_TOKEN deve possuir pelo menos 16 "
                    "caracteres em produção"
                )
            placeholder_values = (
                "change-me",
                "change_me",
                "dev-only",
                "replace-",
                "substitua",
            )
            if any(
                marker in self.auth_secret.lower() for marker in placeholder_values
            ) or any(
                marker in self.auth_bootstrap_token.lower()
                for marker in placeholder_values
            ):
                raise ValueError(
                    "Secrets de produção não podem usar valores de exemplo"
                )
        elif self.auth_required and (
            not self.auth_secret or len(self.auth_secret) < 32
        ):
            raise ValueError(
                "AUTH_SECRET deve possuir pelo menos 32 caracteres quando "
                "a autenticação está ativa"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
