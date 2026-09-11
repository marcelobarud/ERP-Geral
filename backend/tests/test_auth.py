import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import get_settings
from app.main import app
from app.models import Usuario
from app.services.auth import has_permission, hash_password, verify_password


def test_password_hash_is_not_reversible_and_verifies() -> None:
    password = "Senha-forte-de-teste-123"
    encoded = hash_password(password)

    assert password not in encoded
    assert verify_password(password, encoded)
    assert not verify_password("senha-incorreta", encoded)


def test_roles_use_central_permission_matrix() -> None:
    admin = Usuario(
        role="ADMIN", nome="Admin", email="admin@example.com", senha_hash="x"
    )
    manager = Usuario(
        role="MANAGER",
        nome="Manager",
        email="manager@example.com",
        senha_hash="x",
    )
    operator = Usuario(
        role="OPERATOR",
        nome="Operator",
        email="operator@example.com",
        senha_hash="x",
    )

    assert has_permission(admin, "users:manage")
    assert has_permission(manager, "sales:cancel")
    assert not has_permission(operator, "customers:write")


def test_production_requires_authentication_secrets() -> None:
    with pytest.raises(ValidationError):
        from app.core.config import Settings

        Settings(
            database_url="postgresql+psycopg://user:password@localhost:5432/erp_geral",
            environment="production",
        )


def test_protected_operational_endpoint_rejects_missing_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("AUTH_SECRET", "a" * 40)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:password@localhost:5432/erp_geral",
    )
    get_settings.cache_clear()

    try:
        response = TestClient(app).get("/api/customers")
        assert response.status_code == 401
        assert response.json() == {"detail": "Autenticação necessária."}
    finally:
        monkeypatch.delenv("AUTH_REQUIRED", raising=False)
        monkeypatch.delenv("AUTH_SECRET", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)
        get_settings.cache_clear()
