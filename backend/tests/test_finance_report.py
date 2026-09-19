import os
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app
from app.models import (
    ContaFinanceira,
    LiquidacaoFinanceira,
    ParcelaFinanceira,
    TituloFinanceiro,
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


def test_finance_report_adds_period_commitments_and_open_overdue_context(
    client, session
):
    account = ContaFinanceira(nome="Conta relatório financeiro")
    receivable = TituloFinanceiro(
        numero="FIN-RECEBER-ATUAL",
        tipo="RECEBER",
        valor_original=Decimal("100.00"),
        parcelas=[
            ParcelaFinanceira(
                numero=1,
                vencimento=date.today(),
                valor=Decimal("100.00"),
            )
        ],
    )
    overdue_receivable = TituloFinanceiro(
        numero="FIN-RECEBER-VENCIDO",
        tipo="RECEBER",
        valor_original=Decimal("50.00"),
        parcelas=[
            ParcelaFinanceira(
                numero=1,
                vencimento=date.today() - timedelta(days=1),
                valor=Decimal("50.00"),
            )
        ],
    )
    payable = TituloFinanceiro(
        numero="FIN-PAGAR-ATUAL",
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
    paid_overdue = TituloFinanceiro(
        numero="FIN-PAGAR-QUITADO",
        tipo="PAGAR",
        valor_original=Decimal("30.00"),
        parcelas=[
            ParcelaFinanceira(
                numero=1,
                vencimento=date.today() - timedelta(days=2),
                valor=Decimal("30.00"),
            )
        ],
    )
    session.add_all([account, receivable, overdue_receivable, payable, paid_overdue])
    session.flush()
    session.add_all(
        [
            LiquidacaoFinanceira(
                parcela_id=receivable.parcelas[0].id,
                conta_id=account.id,
                valor=Decimal("40.00"),
                data_liquidacao=date.today(),
                status="CONFIRMADA",
            ),
            LiquidacaoFinanceira(
                parcela_id=paid_overdue.parcelas[0].id,
                conta_id=account.id,
                valor=Decimal("30.00"),
                data_liquidacao=date.today(),
                status="CONFIRMADA",
            ),
        ]
    )
    session.flush()

    response = client.get("/api/reports/finance?period=30d")

    assert response.status_code == 200
    payload = response.json()
    assert payload["period"] == "30d"
    assert payload["granularity"] == "day"
    assert len(payload["commitments"]) == 30
    today_bucket = next(
        point
        for point in payload["commitments"]
        if point["bucket"] == date.today().isoformat()
    )
    assert today_bucket["receivable"] == 60.0
    assert today_bucket["payable"] == 80.0
    assert payload["overdue_open_installments"] == 1
    assert payload["overdue_receivable"] == 50.0
    assert payload["overdue_payable"] == 0.0
    assert payload["previsto_receber"] == "110.00"
    assert payload["previsto_pagar"] == "80.00"
    assert payload["realizado_receber"] == "40.00"
    assert payload["realizado_pagar"] == "30.00"


def test_finance_report_preserves_sparse_period_without_fake_values(client):
    response = client.get("/api/reports/finance?period=30d")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["commitments"]) == 30
    assert all(
        point["receivable"] == 0 and point["payable"] == 0
        for point in payload["commitments"]
    )
    assert payload["overdue_open_installments"] == 0
    assert payload["overdue_receivable"] == 0
    assert payload["overdue_payable"] == 0
