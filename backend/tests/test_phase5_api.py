import os
from datetime import date
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


def test_purchase_partial_receipt_updates_stock_once_and_cost_history(
    client, session
) -> None:
    supplier = Fornecedor(
        nome="Fornecedor compras",
        cidade="São Paulo",
        estado="SP",
        rua="Rua A",
        numero="1",
        cnpj="55.555.555/0001-55",
    )
    product = Produto(
        nome="Produto compras",
        categoria="Geral",
        preco_custo=Decimal("10.00"),
        preco_venda=Decimal("15.00"),
        fornecedor=supplier,
    )
    session.add_all([supplier, product])
    session.flush()

    purchase = client.post(
        "/api/purchases",
        json={
            "numero": "PC-TESTE-001",
            "fornecedor_id": supplier.id,
            "itens": [
                {
                    "produto_id": product.id,
                    "quantidade": "10.000",
                    "custo_unitario": "8.50",
                }
            ],
        },
    )
    assert purchase.status_code == 201
    purchase_id = purchase.json()["id"]
    edited = client.patch(
        f"/api/purchases/{purchase_id}",
        json={"observacao": "Entrega fracionada"},
    )
    assert edited.status_code == 200
    assert edited.json()["observacao"] == "Entrega fracionada"
    searched = client.get("/api/purchases?search=PC-TESTE-001")
    assert searched.json()[0]["id"] == purchase_id
    emitted = client.patch(
        f"/api/purchases/{purchase_id}/status", json={"status": "EMITIDO"}
    )
    assert emitted.status_code == 200
    item_id = purchase.json()["itens"][0]["id"]
    receipt = client.post(
        f"/api/purchases/{purchase_id}/receipts",
        json={
            "data_recebimento": date.today().isoformat(),
            "itens": [
                {
                    "pedido_item_id": item_id,
                    "quantidade": "4.000",
                    "custo_efetivo": "8.25",
                }
            ],
        },
    )
    assert receipt.status_code == 201
    assert client.get("/api/finance/titles?tipo=PAGAR").json() == []
    confirmed = client.post(
        f"/api/purchases/receipts/{receipt.json()['id']}/confirm"
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "CONFIRMADO"
    assert purchase_id

    repeated = client.post(
        f"/api/purchases/receipts/{receipt.json()['id']}/confirm"
    )
    assert repeated.status_code == 200
    updated = client.get(f"/api/purchases/{purchase_id}")
    assert updated.json()["status"] == "PARCIALMENTE_RECEBIDO"
    assert Decimal(str(updated.json()["itens"][0]["quantidade_recebida"])) == Decimal(
        "4.000"
    )

    too_much = client.post(
        f"/api/purchases/{purchase_id}/receipts",
        json={
            "data_recebimento": date.today().isoformat(),
            "itens": [
                {
                    "pedido_item_id": item_id,
                    "quantidade": "7.000",
                    "custo_efetivo": "8.25",
                }
            ],
        },
    )
    assert too_much.status_code == 422

    final_receipt = client.post(
        f"/api/purchases/{purchase_id}/receipts",
        json={
            "data_recebimento": date.today().isoformat(),
            "itens": [
                {
                    "pedido_item_id": item_id,
                    "quantidade": "6.000",
                    "custo_efetivo": "8.10",
                }
            ],
        },
    )
    assert final_receipt.status_code == 201
    final_confirmation = client.post(
        f"/api/purchases/receipts/{final_receipt.json()['id']}/confirm"
    )
    assert final_confirmation.status_code == 200
    assert final_confirmation.json()["status"] == "CONFIRMADO"
    completed = client.get(f"/api/purchases/{purchase_id}")
    assert completed.json()["status"] == "RECEBIDO"
    assert Decimal(str(completed.json()["itens"][0]["quantidade_recebida"])) == Decimal(
        "10.000"
    )
    payables = client.get("/api/finance/titles?tipo=PAGAR")
    assert payables.status_code == 200
    assert any(
        item["origem_tipo"] == "RECEBIMENTO_COMPRA"
        and item["origem_id"] == final_receipt.json()["id"]
        for item in payables.json()
    )
    audit = client.get("/api/audit-logs")
    actions = {entry["acao"] for entry in audit.json()}
    assert {
        "purchase_created",
        "purchase_status_changed",
        "receipt_created",
        "receipt_confirmed",
    } <= actions
