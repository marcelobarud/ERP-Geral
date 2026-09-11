import os
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app
from app.models import Cliente

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


def test_finance_installments_partial_payment_reversal_and_cashflow(
    client, session
) -> None:
    customer = Cliente(
        nome="Cliente financeiro",
        cidade="São Paulo",
        estado="SP",
        rua="Rua A",
        numero="1",
    )
    session.add(customer)
    session.flush()
    account = client.get("/api/finance/accounts")
    account_id = account.json()[0]["id"]
    title = client.post(
        "/api/finance/receivables",
        json={
            "cliente_id": customer.id,
            "valor_original": "100.00",
            "vencimentos": [
                date.today().isoformat(),
                (date.today() + timedelta(days=30)).isoformat(),
            ],
        },
    )
    assert title.status_code == 201
    assert sum(
        (Decimal(str(item["valor"])) for item in title.json()["parcelas"]),
        Decimal("0.00"),
    ) == Decimal("100.00")
    installment_id = title.json()["parcelas"][0]["id"]
    payment = client.post(
        f"/api/finance/installments/{installment_id}/settlements",
        json={
            "conta_id": account_id,
            "valor": "25.00",
            "data_liquidacao": date.today().isoformat(),
        },
    )
    assert payment.status_code == 201
    partial = client.get(f"/api/finance/titles/{title.json()['id']}")
    assert partial.json()["status"] == "PARCIAL"
    reversed_payment = client.post(
        f"/api/finance/settlements/{payment.json()['id']}/reverse"
    )
    assert reversed_payment.status_code == 200
    cashflow = client.get("/api/finance/cashflow")
    assert Decimal(str(cashflow.json()["realizado_receber"])) == Decimal("0.00")
