import os

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.session import get_db_session
from app.main import app

pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="defina TEST_DATABASE_URL para executar os testes PostgreSQL",
)


@pytest.fixture
def client(session, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("AUTH_SECRET", "a" * 40)
    get_settings.cache_clear()

    def override_db_session():
        yield session

    app.dependency_overrides[get_db_session] = override_db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    get_settings.cache_clear()


def test_authentication_authorization_inactive_user_and_audit(client):
    bootstrap = client.post(
        "/api/auth/bootstrap",
        json={
            "nome": "Administrador",
            "email": "admin@erp.local",
            "senha": "Senha-admin-123",
        },
    )
    assert bootstrap.status_code == 201
    admin_token = bootstrap.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    invalid_login = client.post(
        "/api/auth/login",
        json={"email": "admin@erp.local", "senha": "senha-incorreta"},
    )
    assert invalid_login.status_code == 401

    create_operator = client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "nome": "Operador",
            "email": "operador@erp.local",
            "senha": "Senha-operador-123",
            "role": "OPERATOR",
        },
    )
    assert create_operator.status_code == 201
    operator_id = create_operator.json()["id"]

    operator_login = client.post(
        "/api/auth/login",
        json={
            "email": "operador@erp.local",
            "senha": "Senha-operador-123",
        },
    )
    assert operator_login.status_code == 200
    operator_headers = {
        "Authorization": f"Bearer {operator_login.json()['access_token']}"
    }

    assert client.get("/api/customers", headers=operator_headers).status_code == 200
    forbidden = client.post(
        "/api/customers",
        headers=operator_headers,
        json={
            "nome": "Cliente bloqueado",
            "cidade": "São Paulo",
            "estado": "SP",
            "rua": "Rua A",
            "numero": "1",
        },
    )
    assert forbidden.status_code == 403

    deactivate = client.patch(
        f"/api/users/{operator_id}",
        headers=admin_headers,
        json={"ativo": False},
    )
    assert deactivate.status_code == 200
    inactive_login = client.post(
        "/api/auth/login",
        json={
            "email": "operador@erp.local",
            "senha": "Senha-operador-123",
        },
    )
    assert inactive_login.status_code == 403

    audit = client.get("/api/audit-logs", headers=admin_headers)
    assert audit.status_code == 200
    actions = {entry["acao"] for entry in audit.json()}
    assert {"bootstrap", "login", "user_created", "role_changed"} <= actions

    assert client.post("/api/auth/logout", headers=admin_headers).status_code == 200
    assert client.get("/api/customers", headers=admin_headers).status_code == 401
