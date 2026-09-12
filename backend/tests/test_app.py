import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.db.session import create_engine_from_settings, create_session_factory
from app.main import app, create_app


def test_fastapi_app_can_be_imported() -> None:
    assert app.title == "ERP Geral"


def test_health_check_returns_minimal_contract() -> None:
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ok", "degraded"}
    assert payload["process"] == "ok"
    assert "database" in payload
    assert "schema" in payload
    assert "expected_migration" in payload


def test_health_check_allows_frontend_local_origin() -> None:
    client = TestClient(app)

    response = client.get(
        "/api/health",
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_production_disables_openapi_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("API_DOCS_ENABLED", raising=False)

    application = create_app()
    client = TestClient(application)

    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_cors_origins_are_configurable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("CORS_ORIGINS", "https://erp.example, https://admin.example")

    application = create_app()
    response = TestClient(application).get(
        "/api/health",
        headers={"Origin": "https://erp.example"},
    )

    assert response.headers["access-control-allow-origin"] == "https://erp.example"


def test_validation_errors_do_not_expose_input_details() -> None:
    application = create_app()

    @application.get("/test-validation")
    def validation_route(value: int) -> int:
        return value

    client = TestClient(application)

    response = client.get("/test-validation", params={"value": "not-an-int"})

    assert response.status_code == 422
    assert response.json() == {"detail": "Dados de entrada inválidos."}
    assert "not-an-int" not in response.text


def test_unhandled_errors_return_generic_response() -> None:
    application = create_app()

    @application.get("/test-error")
    def error_route() -> None:
        raise RuntimeError("internal secret")

    client = TestClient(application, raise_server_exceptions=False)

    response = client.get("/test-error")

    assert response.status_code == 500
    assert response.json() == {"detail": "Erro interno do servidor."}
    assert "internal secret" not in response.text


def test_settings_load_database_url_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:password@localhost:5432/erp_geral",
    )
    get_settings.cache_clear()

    settings = Settings()

    assert settings.database_url.startswith("postgresql+psycopg://")


def test_settings_without_database_url_fail_clearly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_reject_non_postgresql_url() -> None:
    with pytest.raises(ValidationError):
        Settings(database_url="sqlite:///not-supported.db")


def test_sqlalchemy_session_factory_can_open_and_close_without_connecting() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://user:password@localhost:5432/erp_geral"
    )
    engine = create_engine_from_settings(settings)
    session_factory = create_session_factory(engine)
    session = session_factory()

    try:
        assert session.is_active
    finally:
        session.close()
        engine.dispose()
