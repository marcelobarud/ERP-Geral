import os
from datetime import date, datetime, timezone
from decimal import Decimal

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


def test_sale_stock_posting_cancellation_and_partial_return(client, session) -> None:
    supplier = Fornecedor(
        nome="Fornecedor integração",
        cidade="São Paulo",
        estado="SP",
        rua="Rua A",
        numero="1",
        cnpj="66.666.666/0001-66",
    )
    customer = Cliente(
        nome="Cliente integração",
        cidade="São Paulo",
        estado="SP",
        rua="Rua B",
        numero="2",
    )
    employee = Funcionario(
        nome_completo="Funcionário integração",
        cidade="São Paulo",
        estado="SP",
        rua="Rua C",
        numero="3",
        cpf="666.666.666-66",
        data_nascimento=date(1990, 1, 1),
    )
    product = Produto(
        nome="Produto integração",
        categoria="Geral",
        preco_custo=Decimal("10.00"),
        preco_venda=Decimal("15.00"),
        fornecedor=supplier,
    )
    session.add_all([supplier, customer, employee, product])
    session.flush()
    deposit_id = client.get("/api/inventory/deposits").json()[0]["id"]
    client.post(
        "/api/inventory/movements",
        json={
            "produto_id": product.id,
            "deposito_id": deposit_id,
            "tipo": "ENTRADA",
            "quantidade": "5.000",
            "data_movimentacao": datetime.now(timezone.utc).isoformat(),
            "origem": "TESTE",
            "chave_idempotencia": "integracao-entrada",
        },
    )
    sale = client.post(
        "/api/sales",
        json={
            "cliente_id": customer.id,
            "funcionario_id": employee.id,
            "data_venda": datetime.now(timezone.utc).isoformat(),
            "itens": [{"produto_id": product.id, "quantidade": "2.000"}],
        },
    )
    assert sale.status_code == 201
    sale_id = sale.json()["id"]
    posted = client.post(f"/api/sales/{sale_id}/post-stock")
    assert posted.status_code == 200
    repeated = client.post(f"/api/sales/{sale_id}/post-stock")
    assert repeated.status_code == 200
    returned = client.post(
        f"/api/sales/{sale_id}/returns",
        json={
            "motivo": "Devolução parcial",
            "itens": [
                {
                    "venda_item_id": sale.json()["itens"][0]["id"],
                    "quantidade": "1.000",
                }
            ],
        },
    )
    assert returned.status_code == 201
    approved = client.post(
        f"/api/sales/returns/{returned.json()['id']}/approve"
    )
    assert approved.status_code == 200
    cancelled = client.post(f"/api/sales/{sale_id}/cancel", json={})
    assert cancelled.status_code == 200
