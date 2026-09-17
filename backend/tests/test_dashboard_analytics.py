import os
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app
from app.models import (
    Cliente,
    Fornecedor,
    Funcionario,
    ParcelaFinanceira,
    Produto,
    TituloFinanceiro,
    Venda,
    VendaItem,
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


def test_dashboard_analytics_aggregates_real_domains_and_interval(client, session):
    supplier = Fornecedor(
        nome="Fornecedor analytics",
        cidade="São Paulo",
        estado="SP",
        rua="Rua A",
        numero="1",
        cnpj="77.777.777/0001-77",
    )
    customer = Cliente(
        nome="Cliente analytics",
        cidade="São Paulo",
        estado="SP",
        rua="Rua B",
        numero="2",
    )
    employee = Funcionario(
        nome_completo="Funcionário analytics",
        cidade="São Paulo",
        estado="SP",
        rua="Rua C",
        numero="3",
        cpf="777.777.777-77",
        data_nascimento=date(1990, 1, 1),
    )
    product = Produto(
        nome="Produto analytics",
        categoria="Geral",
        preco_custo=Decimal("10.00"),
        preco_venda=Decimal("15.00"),
        fornecedor=supplier,
    )
    session.add_all([supplier, customer, employee, product])
    session.flush()

    sale_date = datetime.combine(
        date.today() - timedelta(days=40), time.min, tzinfo=timezone.utc
    )
    sale = Venda(
        cliente_id=customer.id,
        funcionario_id=employee.id,
        data_venda=sale_date,
        status="CONCLUIDA",
        itens=[
            VendaItem(
                produto_id=product.id,
                quantidade=Decimal("2.000"),
                preco_unitario=Decimal("15.00"),
                fornecedor_id=supplier.id,
            )
        ],
    )
    session.add(sale)

    title = TituloFinanceiro(
        numero="ANALYTICS-PAGAR",
        tipo="PAGAR",
        valor_original=Decimal("80.00"),
        parcelas=[
            ParcelaFinanceira(
                numero=1,
                vencimento=date.today(),
                valor=Decimal("80.00"),
            )
        ],
    )
    session.add(title)
    session.flush()

    response = client.get("/api/reports/dashboard/analytics?period=12m")

    assert response.status_code == 200
    payload = response.json()
    assert payload["period"] == "12m"
    assert payload["granularity"] == "month"
    assert len(payload["sales_trend"]) <= 13
    sales_bucket_date = (date.today() - timedelta(days=40)).replace(day=1)
    sales_bucket = next(
        point
        for point in payload["sales_trend"]
        if point["bucket"] == sales_bucket_date.isoformat()
    )
    assert sales_bucket["sales_value"] == 30.0
    assert sales_bucket["completed_sales"] == 1
    finance_bucket = next(
        point
        for point in payload["finance_trend"]
        if point["bucket"] == date.today().replace(day=1).isoformat()
    )
    assert finance_bucket["receivable"] == 0.0
    assert finance_bucket["payable"] == 80.0
    assert payload["stock_attention"] == []

    short_response = client.get("/api/reports/dashboard/analytics?period=30d")

    assert short_response.status_code == 200
    short_payload = short_response.json()
    assert short_payload["granularity"] == "day"
    assert len(short_payload["sales_trend"]) == 30


def test_dashboard_analytics_returns_empty_period_without_fake_values(client):
    response = client.get("/api/reports/dashboard/analytics?period=30d")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["sales_trend"]) == 30
    assert all(point["sales_value"] == 0 for point in payload["sales_trend"])
    assert all(
        point["receivable"] == 0 and point["payable"] == 0
        for point in payload["finance_trend"]
    )
    assert payload["stock_attention"] == []
