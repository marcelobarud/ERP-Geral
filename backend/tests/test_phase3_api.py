import os
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app
from app.models import Cliente, CondicaoPagamento, Fornecedor, Funcionario, Produto

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


def test_quote_order_and_sale_conversion_are_controlled(client, session) -> None:
    supplier = Fornecedor(
        nome="Fornecedor comercial",
        cidade="São Paulo",
        estado="SP",
        rua="Rua A",
        numero="1",
        cnpj="33.333.333/0001-33",
    )
    customer = Cliente(
        nome="Cliente comercial",
        cidade="São Paulo",
        estado="SP",
        rua="Rua B",
        numero="2",
    )
    employee = Funcionario(
        nome_completo="Funcionário comercial",
        cidade="São Paulo",
        estado="SP",
        rua="Rua C",
        numero="3",
        cpf="333.333.333-33",
        data_nascimento=date(1990, 1, 1),
    )
    product = Produto(
        nome="Produto comercial",
        categoria="Geral",
        preco_custo=Decimal("10.00"),
        preco_venda=Decimal("15.00"),
        fornecedor=supplier,
    )
    payment_condition = CondicaoPagamento(
        codigo="PIX-TESTE", nome="Pix à vista", descricao="Pagamento imediato"
    )
    session.add_all([supplier, customer, employee, product, payment_condition])
    session.flush()

    quote = client.post(
        "/api/commercial/quotes",
        json={
            "numero": "ORC-TESTE-001",
            "cliente_id": customer.id,
            "funcionario_id": employee.id,
            "condicao_pagamento_id": payment_condition.id,
            "desconto": "1.00",
            "frete": "5.00",
            "itens": [{"produto_id": product.id, "quantidade": "2.000"}],
        },
    )
    assert quote.status_code == 201
    assert Decimal(str(quote.json()["total"])) == Decimal("34.00")

    invalid_transition = client.patch(
        f"/api/commercial/quotes/{quote.json()['id']}/status",
        json={"status": "APROVADO"},
    )
    assert invalid_transition.status_code == 409

    for quote_status in ("ENVIADO", "APROVADO"):
        transition = client.patch(
            f"/api/commercial/quotes/{quote.json()['id']}/status",
            json={"status": quote_status},
        )
        assert transition.status_code == 200

    order = client.post(
        f"/api/commercial/quotes/{quote.json()['id']}/convert-to-order"
    )
    assert order.status_code == 200
    assert order.json()["orcamento_id"] == quote.json()["id"]

    repeated_order = client.post(
        f"/api/commercial/quotes/{quote.json()['id']}/convert-to-order"
    )
    assert repeated_order.status_code == 200
    assert repeated_order.json()["id"] == order.json()["id"]

    order_status = client.patch(
        f"/api/commercial/orders/{order.json()['id']}/status",
        json={"status": "CONFIRMADO"},
    )
    assert order_status.status_code == 200

    sale = client.post(
        f"/api/commercial/orders/{order.json()['id']}/convert-to-sale"
    )
    assert sale.status_code == 200
    assert Decimal(str(sale.json()["itens"][0]["preco_unitario"])) == Decimal("15.00")
    assert sale.json()["pedido_id"] == order.json()["id"]
    assert sale.json()["condicao_pagamento_id"] == payment_condition.id

    repeated_sale = client.post(
        f"/api/commercial/orders/{order.json()['id']}/convert-to-sale"
    )
    assert repeated_sale.status_code == 200
    assert repeated_sale.json()["id"] == sale.json()["id"]

    printable = client.get(
        f"/api/commercial/quotes/{quote.json()['id']}/print"
    )
    assert printable.status_code == 200
    assert printable.headers["content-type"].startswith("text/html")
    assert "ORC-TESTE-001" in printable.text
