import os
from datetime import date
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


def seed_catalog_dependencies(session):
    supplier = Fornecedor(
        nome="Fornecedor catálogo",
        cidade="São Paulo",
        estado="SP",
        rua="Rua A",
        numero="1",
        cnpj="11.111.111/0001-11",
    )
    second_supplier = Fornecedor(
        nome="Segundo fornecedor catálogo",
        cidade="São Paulo",
        estado="SP",
        rua="Rua B",
        numero="2",
        cnpj="22.222.222/0001-22",
    )
    customer = Cliente(
        nome="Cliente catálogo",
        cidade="São Paulo",
        estado="SP",
        rua="Rua C",
        numero="3",
    )
    employee = Funcionario(
        nome_completo="Funcionário catálogo",
        cidade="São Paulo",
        estado="SP",
        rua="Rua D",
        numero="4",
        cpf="111.111.111-11",
        data_nascimento=date(1990, 1, 1),
    )
    session.add_all([supplier, second_supplier, customer, employee])
    session.flush()
    return supplier, second_supplier, customer, employee


def test_product_catalog_supports_sku_categories_units_and_multiple_suppliers(
    client: TestClient, session
) -> None:
    supplier, second_supplier, _, _ = seed_catalog_dependencies(session)

    category = client.post("/api/catalog/categories", json={"nome": "Bebidas"})
    assert category.status_code == 201
    units = client.get("/api/catalog/units")
    assert units.status_code == 200
    assert any(unit["codigo"] == "UN" for unit in units.json())

    product = client.post(
        "/api/products",
        json={
            "nome": "Produto catalogado",
            "sku": "BEB-001",
            "codigo_barras": "789000000001",
            "categoria": "Bebidas",
            "categoria_id": category.json()["id"],
            "unidade_medida": "UN",
            "estoque_minimo": "5.000",
            "preco_custo": "10.00",
            "preco_venda": "15.00",
            "fornecedor_id": supplier.id,
        },
    )
    assert product.status_code == 201
    assert product.json()["sku"] == "BEB-001"
    product_id = product.json()["id"]

    duplicate = client.post(
        "/api/products",
        json={
            **product.json(),
            "nome": "Produto duplicado",
            "campos_personalizados": {},
        },
    )
    assert duplicate.status_code == 409

    related = client.post(
        f"/api/catalog/products/{product_id}/suppliers",
        json={
            "fornecedor_id": second_supplier.id,
            "custo_referencia": "9.50",
        },
    )
    assert related.status_code == 201
    links = client.get(f"/api/catalog/products/{product_id}/suppliers")
    assert links.status_code == 200
    assert {link["fornecedor_id"] for link in links.json()} == {
        supplier.id,
        second_supplier.id,
    }
    assert sum(link["preferencial"] for link in links.json()) == 1


def test_inactive_product_is_not_accepted_in_new_sale(
    client: TestClient, session
) -> None:
    supplier, _, customer, employee = seed_catalog_dependencies(session)
    product = Produto(
        nome="Produto inativo",
        categoria="Geral",
        preco_custo=Decimal("10.00"),
        preco_venda=Decimal("15.00"),
        fornecedor_id=supplier.id,
        ativo=False,
    )
    session.add(product)
    session.flush()

    response = client.post(
        "/api/sales",
        json={
            "cliente_id": customer.id,
            "funcionario_id": employee.id,
            "data_venda": "2026-09-11T10:00:00Z",
            "itens": [{"produto_id": product.id, "quantidade": "1.000"}],
        },
    )
    assert response.status_code == 422
    assert "inativo" in response.json()["detail"]
