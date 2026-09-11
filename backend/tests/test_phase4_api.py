import os
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app
from app.models import Fornecedor, Produto

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


def test_stock_movements_balance_negative_protection_reversal_and_inventory(
    client, session
) -> None:
    supplier = Fornecedor(
        nome="Fornecedor estoque",
        cidade="São Paulo",
        estado="SP",
        rua="Rua A",
        numero="1",
        cnpj="44.444.444/0001-44",
    )
    product = Produto(
        nome="Produto estoque",
        categoria="Geral",
        preco_custo=Decimal("10.00"),
        preco_venda=Decimal("15.00"),
        fornecedor=supplier,
    )
    session.add_all([supplier, product])
    session.flush()

    deposit = client.get("/api/inventory/deposits")
    assert deposit.status_code == 200
    deposit_id = deposit.json()[0]["id"]
    renamed_deposit = client.patch(
        f"/api/inventory/deposits/{deposit_id}",
        json={"nome": "Depósito principal operacional"},
    )
    assert renamed_deposit.status_code == 200
    assert renamed_deposit.json()["padrao"] is True
    movement_payload = {
        "produto_id": product.id,
        "deposito_id": deposit_id,
        "tipo": "ENTRADA",
        "quantidade": "10.000",
        "data_movimentacao": datetime.now(timezone.utc).isoformat(),
        "origem": "TESTE",
        "chave_idempotencia": "entrada-produto-estoque",
    }
    entry = client.post("/api/inventory/movements", json=movement_payload)
    assert entry.status_code == 201
    repeated = client.post("/api/inventory/movements", json=movement_payload)
    assert repeated.status_code == 201
    assert repeated.json()["id"] == entry.json()["id"]

    balance = client.get(
        f"/api/inventory/balances?deposit_id={deposit_id}&product_id={product.id}"
    )
    assert Decimal(str(balance.json()[0]["saldo"])) == Decimal("10.000")

    exit_response = client.post(
        "/api/inventory/movements",
        json={
            **movement_payload,
            "tipo": "SAIDA",
            "quantidade": "4.000",
            "chave_idempotencia": "saida-produto-estoque",
        },
    )
    assert exit_response.status_code == 201
    negative = client.post(
        "/api/inventory/movements",
        json={
            **movement_payload,
            "tipo": "SAIDA",
            "quantidade": "7.000",
            "chave_idempotencia": "saida-negativa-estoque",
        },
    )
    assert negative.status_code == 409

    reversal = client.post(
        "/api/inventory/movements",
        json={
            **movement_payload,
            "tipo": "REVERSAO",
            "quantidade": "4.000",
            "movimento_origem_id": exit_response.json()["id"],
            "chave_idempotencia": "reversao-saida-estoque",
        },
    )
    assert reversal.status_code == 201

    inventory = client.post(
        "/api/inventory/inventories",
        json={
            "deposito_id": deposit_id,
            "data_inventario": date.today().isoformat(),
            "observacao": "Contagem de teste",
            "itens": [{"produto_id": product.id, "quantidade_contada": "3.000"}],
        },
    )
    assert inventory.status_code == 201
    inventories = client.get("/api/inventory/inventories")
    assert inventories.status_code == 200
    assert inventories.json()[0]["id"] == inventory.json()["id"]
    confirmed = client.post(
        f"/api/inventory/inventories/{inventory.json()['id']}/confirm"
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "CONFIRMADO"
    repeated_confirmation = client.post(
        f"/api/inventory/inventories/{inventory.json()['id']}/confirm"
    )
    assert repeated_confirmation.status_code == 200

    final_balance = client.get(
        f"/api/inventory/balances?deposit_id={deposit_id}&product_id={product.id}"
    )
    assert Decimal(str(final_balance.json()[0]["saldo"])) == Decimal("3.000")
