from fastapi.testclient import TestClient

from app.main import app


def test_openapi_lists_sales_routes_and_sale_request_contract() -> None:
    client = TestClient(app)

    assert client.get("/docs").status_code == 200
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/health" in paths
    assert "/api/sales" in paths
    assert "/api/sales/{sale_id}" in paths
    assert "get" in paths["/api/sales"]
    assert "post" in paths["/api/sales"]
    assert "get" in paths["/api/sales/{sale_id}"]
    assert "/api/sales/{sale_id}/cancel" in paths
    assert "post" in paths["/api/sales/{sale_id}/cancel"]

    sale_schema = response.json()["components"]["schemas"]["VendaCreate"]
    assert set(sale_schema["required"]) == {
        "cliente_id",
        "funcionario_id",
        "data_venda",
        "itens",
    }
    assert "preco_unitario" not in sale_schema["properties"]

    employee_schema = response.json()["components"]["schemas"]["FuncionarioRead"]
    assert employee_schema["properties"]["ativo"]["type"] == "boolean"
    employee_update_schema = response.json()["components"]["schemas"][
        "FuncionarioUpdate"
    ]
    assert {
        item["type"] for item in employee_update_schema["properties"]["ativo"]["anyOf"]
    } == {
        "boolean",
        "null",
    }

    sale_item_read_schema = response.json()["components"]["schemas"]["VendaItemRead"]
    assert sale_item_read_schema["properties"]["fornecedor_id"]["type"] == "integer"
    assert sale_item_read_schema["properties"]["fornecedor"]["$ref"].endswith(
        "/FornecedorResumo"
    )
    sale_item_create_schema = response.json()["components"]["schemas"][
        "VendaItemCreate"
    ]
    assert "fornecedor_id" not in sale_item_create_schema["properties"]

    customer_detail_schema = response.json()["components"]["schemas"][
        "ClienteDetailRead"
    ]
    assert customer_detail_schema["properties"]["produtos_comprados"]["type"] == "array"
    customer_product_ref = customer_detail_schema["properties"]["produtos_comprados"][
        "items"
    ]["$ref"]
    assert customer_product_ref.endswith("/ClienteProdutoCompradoRead")
    supplier_detail_schema = response.json()["components"]["schemas"][
        "FornecedorDetailRead"
    ]
    assert supplier_detail_schema["properties"]["produtos"]["type"] == "array"
    supplier_product_ref = supplier_detail_schema["properties"]["produtos"][
        "items"
    ]["$ref"]
    assert supplier_product_ref.endswith("/FornecedorProdutoRead")

    employee_parameters = response.json()["paths"]["/api/employees"]["get"][
        "parameters"
    ]
    assert {parameter["name"] for parameter in employee_parameters} >= {
        "active",
        "search",
        "city",
        "state",
    }

    expected_list_filters = {
        "/api/customers": {"search", "city", "state"},
        "/api/products": {
            "search",
            "category",
            "supplier_id",
            "cost_min",
            "cost_max",
            "sale_price_min",
            "sale_price_max",
        },
        "/api/suppliers": {"search", "city", "state"},
        "/api/sales": {
            "search",
            "product_id",
            "customer_id",
            "employee_id",
            "date_from",
            "date_to",
            "total_min",
            "total_max",
            "status",
        },
    }
    for path, expected_parameters in expected_list_filters.items():
        parameters = response.json()["paths"][path]["get"]["parameters"]
        assert {parameter["name"] for parameter in parameters} >= (
            expected_parameters | {"page", "page_size"}
        )

    assert "/api/dashboard/summary" in paths
    assert "/api/auth/login" in paths
    assert "/api/auth/logout" in paths
    assert "/api/auth/me" in paths
    assert "/api/users" in paths
    assert "/api/audit-logs" in paths
    dashboard_properties = response.json()["components"]["schemas"][
        "DashboardSummaryRead"
    ]["properties"]
    assert set(dashboard_properties) == {
        "customers",
        "products",
        "suppliers",
        "employees",
        "sales",
    }
