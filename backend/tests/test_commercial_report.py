import os
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app
from app.models import Cliente, Fornecedor, Funcionario, Produto, Venda, VendaItem

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


def test_commercial_report_adds_temporal_reading_and_named_rankings(client, session):
    supplier = Fornecedor(
        nome="Fornecedor relatório comercial",
        cidade="São Paulo",
        estado="SP",
        rua="Rua A",
        numero="1",
        cnpj="88.888.888/0001-88",
    )
    customer = Cliente(
        nome="Cliente relatório comercial",
        cidade="São Paulo",
        estado="SP",
        rua="Rua B",
        numero="2",
    )
    employee = Funcionario(
        nome_completo="Funcionário relatório comercial",
        cidade="São Paulo",
        estado="SP",
        rua="Rua C",
        numero="3",
        cpf="888.888.888-88",
        data_nascimento=date(1990, 1, 1),
    )
    first_product = Produto(
        nome="Produto líder",
        categoria="Geral",
        preco_custo=Decimal("10.00"),
        preco_venda=Decimal("15.00"),
        fornecedor=supplier,
    )
    second_product = Produto(
        nome="Produto apoio",
        categoria="Geral",
        preco_custo=Decimal("5.00"),
        preco_venda=Decimal("8.00"),
        fornecedor=supplier,
    )
    session.add_all([supplier, customer, employee, first_product, second_product])
    session.flush()

    start = date.today() - timedelta(days=3)
    first_sale = Venda(
        cliente_id=customer.id,
        funcionario_id=employee.id,
        data_venda=datetime.combine(start, time.min, tzinfo=timezone.utc),
        status="CONCLUIDA",
        itens=[
            VendaItem(
                produto_id=first_product.id,
                quantidade=Decimal("2.000"),
                preco_unitario=Decimal("15.00"),
                fornecedor_id=supplier.id,
            )
        ],
    )
    second_sale = Venda(
        cliente_id=customer.id,
        funcionario_id=employee.id,
        data_venda=datetime.combine(date.today(), time.min, tzinfo=timezone.utc),
        status="CONCLUIDA",
        itens=[
            VendaItem(
                produto_id=second_product.id,
                quantidade=Decimal("1.000"),
                preco_unitario=Decimal("8.00"),
                fornecedor_id=supplier.id,
            )
        ],
    )
    session.add_all([first_sale, second_sale])

    response = client.get(
        f"/api/reports/commercial?date_from={start.isoformat()}&date_to={date.today().isoformat()}"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["granularity"] == "day"
    assert len(payload["sales_trend"]) == 4
    assert next(
        point
        for point in payload["sales_trend"]
        if point["bucket"] == start.isoformat()
    )["sales_value"] == 30.0
    assert next(
        point
        for point in payload["sales_trend"]
        if point["bucket"] == date.today().isoformat()
    )["sales_value"] == 8.0
    assert payload["by_product"][0]["product_name"] == "Produto líder"
    assert payload["by_product"][0]["total"] == 30.0
    assert payload["by_customer"][0]["customer_name"] == "Cliente relatório comercial"
