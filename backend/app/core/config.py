from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(description="URL de conexão do PostgreSQL")
    app_name: str = "ERP Geral"
    environment: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
