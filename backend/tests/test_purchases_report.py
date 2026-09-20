import os
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app
from app.models import (
    Fornecedor,
    PedidoCompra,
    PedidoCompraItem,
    Produto,
    RecebimentoCompra,
    RecebimentoCompraItem,
)

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


def test_purchases_report_preserves_statuses_receipts_and_cost_values(
    client, session
):
    supplier = Fornecedor(
        nome="Fornecedor relatório compras",
        cidade="São Paulo",
        estado="SP",
        rua="Rua Compras",
        numero="20",
        cnpj="77.777.777/0001-77",
    )
    product = Produto(
        nome="Produto relatório compras",
        sku="COMPRAS-001",
        categoria="Geral",
        unidade_medida="UN",
        estoque_minimo=Decimal("0.000"),
        preco_custo=Decimal("8.00"),
        preco_venda=Decimal("12.00"),
        fornecedor=supplier,
    )
    purchase = PedidoCompra(
        numero="PC-RELATORIO-001",
        fornecedor=supplier,
        status="PARCIALMENTE_RECEBIDO",
        itens=[
            PedidoCompraItem(
                produto=product,
                produto_nome=product.nome,
                sku=product.sku,
                quantidade=Decimal("10.000"),
                quantidade_recebida=Decimal("4.000"),
                custo_unitario=Decimal("8.50"),
            )
        ],
    )
    session.add(purchase)
    session.flush()
    session.add(
        RecebimentoCompra(
            pedido=purchase,
            data_recebimento=date.today(),
            status="CONFIRMADO",
            itens=[
                RecebimentoCompraItem(
                    pedido_item_id=purchase.itens[0].id,
                    produto_id=product.id,
                    quantidade=Decimal("4.000"),
                    custo_efetivo=Decimal("8.25"),
                )
            ],
        )
    )
    session.flush()

    response = client.get("/api/reports/purchases?period=30d")

    assert response.status_code == 200
    payload = response.json()
    assert payload["period_orders"] == 1
    assert payload["received_orders_in_period"] == 1
    assert payload["confirmed_receipts_in_period"] == 1
    assert payload["ordered_value_in_period"] == 85.0
    assert payload["received_value_in_period"] == 33.0
    assert payload["pending_value"] == 51.0
    assert payload["pending_line_count"] == 1
    assert payload["pending_receipts"] == 1
    assert payload["open_orders"] == 1
    assert payload["status_counts"]["PARCIALMENTE_RECEBIDO"] == 1
    assert payload["orders"][0]["supplier_name"] == supplier.nome
    assert payload["orders"][0]["pending_value"] == 51.0


def test_purchases_report_returns_explicit_empty_period(client):
    response = client.get("/api/reports/purchases?period=30d")

    assert response.status_code == 200
    payload = response.json()
    assert payload["period_orders"] == 0
    assert payload["orders"] == []
    assert payload["ordered_value_in_period"] == 0.0
    assert payload["received_orders_in_period"] == 0
    assert payload["status_counts"] == {
        "RASCUNHO": 0,
        "EMITIDO": 0,
        "PARCIALMENTE_RECEBIDO": 0,
        "RECEBIDO": 0,
        "CANCELADO": 0,
    }


def test_purchases_report_rejects_unknown_period(client):
    response = client.get("/api/reports/purchases?period=invalid")

    assert response.status_code == 422
