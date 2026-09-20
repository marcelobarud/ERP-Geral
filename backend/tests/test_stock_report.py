import os
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import get_db_session
from app.main import app
from app.models import (
    DepositoEstoque,
    Fornecedor,
    MovimentacaoEstoque,
    Produto,
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


def test_stock_report_adds_current_position_and_directional_movement_series(
    client, session
):
    deposit = session.scalar(
        select(DepositoEstoque).where(DepositoEstoque.padrao.is_(True))
    )
    supplier = Fornecedor(
        nome="Fornecedor relatório estoque",
        cidade="São Paulo",
        estado="SP",
        rua="Rua Estoque",
        numero="10",
        cnpj="66.666.666/0001-66",
    )
    normal = Produto(
        nome="Produto com saldo normal",
        sku="ESTOQUE-NORMAL",
        categoria="Geral",
        unidade_medida="UN",
        estoque_minimo=Decimal("4.000"),
        preco_custo=Decimal("5.00"),
        preco_venda=Decimal("8.00"),
        fornecedor=supplier,
    )
    critical = Produto(
        nome="Produto crítico",
        sku="ESTOQUE-CRITICO",
        categoria="Geral",
        unidade_medida="KG",
        estoque_minimo=Decimal("10.000"),
        preco_custo=Decimal("7.00"),
        preco_venda=Decimal("11.00"),
        fornecedor=supplier,
    )
    zero_minimum = Produto(
        nome="Produto sem mínimo configurado",
        sku="ESTOQUE-SEM-MINIMO",
        categoria="Geral",
        unidade_medida="L",
        estoque_minimo=Decimal("0.000"),
        preco_custo=Decimal("2.00"),
        preco_venda=Decimal("4.00"),
        fornecedor=supplier,
    )
    session.add_all([supplier, normal, critical, zero_minimum])
    session.flush()
    movement_date = datetime.combine(date.today(), time.min, tzinfo=timezone.utc)
    entry = MovimentacaoEstoque(
        produto_id=normal.id,
        deposito_id=deposit.id,
        tipo="ENTRADA",
        quantidade=Decimal("10.000"),
        data_movimentacao=movement_date,
        origem="RECEBIMENTO_COMPRA",
    )
    exit_movement = MovimentacaoEstoque(
        produto_id=normal.id,
        deposito_id=deposit.id,
        tipo="SAIDA",
        quantidade=Decimal("2.000"),
        data_movimentacao=movement_date,
        origem="VENDA",
    )
    inventory_adjustment = MovimentacaoEstoque(
        produto_id=critical.id,
        deposito_id=deposit.id,
        tipo="AJUSTE_ENTRADA",
        quantidade=Decimal("3.000"),
        data_movimentacao=movement_date,
        origem="INVENTARIO",
        documento_tipo="INVENTARIO",
        documento_id=1,
        observacao="Ajuste confirmado pelo inventário",
    )
    session.add_all([entry, exit_movement, inventory_adjustment])
    session.flush()
    session.add(
        MovimentacaoEstoque(
            produto_id=normal.id,
            deposito_id=deposit.id,
            tipo="REVERSAO",
            quantidade=Decimal("2.000"),
            data_movimentacao=movement_date,
            origem="REVERSAO_VENDA",
            movimento_origem_id=exit_movement.id,
        )
    )
    session.flush()

    response = client.get("/api/reports/stock?period=30d")

    assert response.status_code == 200
    payload = response.json()
    assert payload["period"] == "30d"
    assert payload["granularity"] == "day"
    assert payload["active_products"] == 3
    assert payload["products_with_balance"] == 2
    assert payload["movement_count"] == 4
    assert payload["movement_count_in_period"] == 4
    assert payload["movement_entries"] == 3
    assert payload["movement_exits"] == 1
    assert len(payload["movement_series"]) == 30
    today_bucket = next(
        point
        for point in payload["movement_series"]
        if point["bucket"] == date.today().isoformat()
    )
    assert today_bucket == {
        "bucket": date.today().isoformat(),
        "entries": 3,
        "exits": 1,
    }
    critical_item = next(
        item for item in payload["balances"] if item["produto_id"] == critical.id
    )
    assert critical_item["saldo"] == 3.0
    assert critical_item["deficit"] == 7.0
    assert critical_item["shortfall_percent"] == 70.0
    assert critical_item["unit"] == "KG"
    zero_minimum_item = next(
        item for item in payload["balances"] if item["produto_id"] == zero_minimum.id
    )
    assert zero_minimum_item["shortfall_percent"] is None
    assert len(payload["below_minimum"]) == 1


def test_stock_report_preserves_empty_period_and_additive_contract(client):
    response = client.get("/api/reports/stock?period=30d")

    assert response.status_code == 200
    payload = response.json()
    assert payload["balances"] == []
    assert payload["below_minimum"] == []
    assert payload["movement_count"] == 0
    assert payload["movement_count_in_period"] == 0
    assert len(payload["movement_series"]) == 30
    assert all(
        point["entries"] == 0 and point["exits"] == 0
        for point in payload["movement_series"]
    )
    assert payload["deposit"]["code"] == "PRINCIPAL"


def test_stock_report_groups_daily_boundaries_in_utc(client, session):
    deposit = session.scalar(
        select(DepositoEstoque).where(DepositoEstoque.padrao.is_(True))
    )
    supplier = Fornecedor(
        nome="Fornecedor fronteira UTC",
        cidade="São Paulo",
        estado="SP",
        rua="Rua UTC",
        numero="11",
        cnpj="55.555.555/0001-55",
    )
    product = Produto(
        nome="Produto fronteira UTC",
        sku="ESTOQUE-UTC-FRONTEIRA",
        categoria="Geral",
        unidade_medida="UN",
        preco_custo=Decimal("5.00"),
        preco_venda=Decimal("8.00"),
        fornecedor=supplier,
    )
    session.add_all([supplier, product])
    session.flush()

    today_at_midnight = datetime.combine(
        date.today(), time.min, tzinfo=timezone.utc
    )
    session.add_all(
        [
            MovimentacaoEstoque(
                produto_id=product.id,
                deposito_id=deposit.id,
                tipo="ENTRADA",
                quantidade=Decimal("1.000"),
                data_movimentacao=today_at_midnight - timedelta(minutes=1),
                origem="RECEBIMENTO_COMPRA",
            ),
            MovimentacaoEstoque(
                produto_id=product.id,
                deposito_id=deposit.id,
                tipo="SAIDA",
                quantidade=Decimal("1.000"),
                data_movimentacao=today_at_midnight,
                origem="VENDA",
            ),
        ]
    )
    session.flush()

    response = client.get("/api/reports/stock?period=30d")

    assert response.status_code == 200
    series = response.json()["movement_series"]
    previous_bucket = next(
        point
        for point in series
        if point["bucket"] == (date.today() - timedelta(days=1)).isoformat()
    )
    today_bucket = next(
        point for point in series if point["bucket"] == date.today().isoformat()
    )
    assert previous_bucket == {
        "bucket": (date.today() - timedelta(days=1)).isoformat(),
        "entries": 1,
        "exits": 0,
    }
    assert today_bucket == {
        "bucket": date.today().isoformat(),
        "entries": 0,
        "exits": 1,
    }


def test_stock_report_rejects_unknown_period(client):
    response = client.get("/api/reports/stock?period=invalid")

    assert response.status_code == 422
