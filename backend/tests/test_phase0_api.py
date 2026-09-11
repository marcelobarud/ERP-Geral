import os
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app
from app.models import Cliente, Fornecedor, Funcionario, Produto

pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="defina TEST_DATABASE_URL para executar os testes PostgreSQL",
)


@pytest.fixture
def client(session):
    def override_db_session():
        yield session

    app.dependency_overrides[get_db_session] = override_db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_pagination_and_dashboard_summary_use_backend_aggregates(client, session):
    supplier = Fornecedor(
        nome="Fornecedor Fase 0",
        cidade="São Paulo",
        estado="SP",
        rua="Rua A",
        numero="1",
        cnpj="12.345.678/0001-90",
    )
    employees = [
        Funcionario(
            nome_completo=f"Funcionário {index}",
            cidade="São Paulo",
            estado="SP",
            rua="Rua B",
            numero=str(index),
            cpf=f"123.456.789-{index:02d}",
            data_nascimento=date(1990, 1, index),
        )
        for index in (1, 2, 3)
    ]
    customers = [
        Cliente(
            nome=f"Cliente {index}",
            cidade="São Paulo",
            estado="SP",
            rua="Rua C",
            numero=str(index),
        )
        for index in (1, 2, 3)
    ]
    product = Produto(
        nome="Produto Fase 0",
        categoria="Geral",
        preco_custo="10.00",
        preco_venda="15.00",
        fornecedor=supplier,
    )
    session.add_all([supplier, *employees, *customers, product])
    session.flush()

    page = client.get("/api/customers?page=2&page_size=2")
    assert page.status_code == 200
    assert page.json()["page"] == 2
    assert page.json()["page_size"] == 2
    assert page.json()["total"] == 3
    assert page.json()["total_pages"] == 2
    assert len(page.json()["items"]) == 1

    summary = client.get("/api/dashboard/summary")
    assert summary.status_code == 200
    assert summary.json() == {
        "customers": 3,
        "products": 1,
        "suppliers": 1,
        "employees": 3,
        "sales": 0,
    }
