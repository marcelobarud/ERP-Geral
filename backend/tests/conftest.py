import os

import pytest
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

REQUIRED_TABLES = {
    "alembic_version",
    "clientes",
    "fornecedores",
    "funcionarios",
    "produtos",
    "vendas",
    "venda_itens",
    "configuracoes_aparencia",
    "configuracoes_aparencia_paginas",
    "configuracoes_aparencia_elementos",
    "cliente_campos",
    "cliente_campos_valores",
    "produto_campos",
    "produto_campos_valores",
    "funcionario_campos",
    "funcionario_campos_valores",
    "fornecedor_campos",
    "fornecedor_campos_valores",
    "usuarios",
    "sessoes_autenticacao",
    "logs_auditoria",
    "unidades_medida",
    "categorias_produto",
    "produtos_fornecedores",
    "historicos_custo_produto",
    "condicoes_pagamento",
    "orcamentos",
    "orcamento_itens",
    "pedidos_venda",
    "pedido_venda_itens",
    "depositos_estoque",
    "configuracoes_estoque",
    "movimentacoes_estoque",
    "inventarios_estoque",
    "inventarios_estoque_itens",
    "pedidos_compra",
    "pedido_compra_itens",
    "recebimentos_compra",
    "recebimentos_compra_itens",
    "devolucoes_venda",
    "devolucoes_venda_itens",
    "categorias_financeiras",
    "contas_financeiras",
    "titulos_financeiros",
    "parcelas_financeiras",
    "liquidacoes_financeiras",
    "modulos_erp",
}
EXPECTED_MIGRATION = "20260911_0011"

REFERENCE_DATA_SQL = (
    "INSERT INTO unidades_medida (codigo, nome) VALUES "
    "('UN', 'Unidade'), ('KG', 'Quilograma'), ('G', 'Grama'), "
    "('L', 'Litro'), ('ML', 'Mililitro'), ('M', 'Metro'), "
    "('M2', 'Metro quadrado'), ('CX', 'Caixa')",
    "INSERT INTO contas_financeiras (nome) VALUES ('Caixa principal')",
    "INSERT INTO modulos_erp (codigo, nome, ordem) VALUES "
    "('commercial', 'Comercial', 10), ('purchases', 'Compras', 20), "
    "('inventory', 'Estoque', 30), ('finance', 'Financeiro', 40), "
    "('reports', 'Relatórios', 50)",
    "INSERT INTO depositos_estoque "
    "(codigo, nome, ativo, padrao, created_at, updated_at) VALUES "
    "('PRINCIPAL', 'Depósito principal', TRUE, TRUE, "
    "CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
    "INSERT INTO configuracoes_estoque "
    "(id, permitir_saldo_negativo, updated_at) VALUES (1, FALSE, CURRENT_TIMESTAMP)",
)

TEST_DATA_TABLES = (
    "logs_auditoria",
    "sessoes_autenticacao",
    "usuarios",
    "historicos_custo_produto",
    "pedido_venda_itens",
    "pedidos_venda",
    "orcamento_itens",
    "orcamentos",
    "condicoes_pagamento",
    "inventarios_estoque_itens",
    "inventarios_estoque",
    "movimentacoes_estoque",
    "configuracoes_estoque",
    "depositos_estoque",
    "recebimentos_compra_itens",
    "recebimentos_compra",
    "pedido_compra_itens",
    "pedidos_compra",
    "devolucoes_venda_itens",
    "devolucoes_venda",
    "liquidacoes_financeiras",
    "parcelas_financeiras",
    "titulos_financeiros",
    "contas_financeiras",
    "categorias_financeiras",
    "modulos_erp",
    "produtos_fornecedores",
    "categorias_produto",
    "unidades_medida",
    "cliente_campos_valores",
    "produto_campos_valores",
    "funcionario_campos_valores",
    "fornecedor_campos_valores",
    "cliente_campos",
    "produto_campos",
    "funcionario_campos",
    "fornecedor_campos",
    "configuracoes_aparencia",
    "configuracoes_aparencia_paginas",
    "configuracoes_aparencia_elementos",
    "venda_itens",
    "vendas",
    "produtos",
    "funcionarios",
    "clientes",
    "fornecedores",
)


@pytest.fixture(scope="session")
def test_engine():
    test_database_url = os.getenv("TEST_DATABASE_URL")
    if test_database_url is None:
        pytest.skip("TEST_DATABASE_URL não foi definida")
    try:
        database_url = make_url(test_database_url)
    except Exception:
        pytest.fail("TEST_DATABASE_URL possui formato inválido")
    if (
        database_url.get_backend_name() != "postgresql"
        or database_url.get_driver_name() != "psycopg"
    ):
        pytest.fail("TEST_DATABASE_URL deve usar PostgreSQL com o driver psycopg")
    if not database_url.database or not database_url.database.endswith("_test"):
        pytest.fail("TEST_DATABASE_URL deve apontar para um banco com sufixo _test")

    engine = create_engine(test_database_url)
    try:
        with engine.connect() as connection:
            connection.execute(select(1))
    except Exception:
        engine.dispose()
        pytest.fail(
            "Não foi possível conectar ao PostgreSQL de teste; "
            "verifique TEST_DATABASE_URL, o serviço e as credenciais locais."
        )

    with engine.connect() as connection:
        missing_tables = REQUIRED_TABLES - set(inspect(connection).get_table_names())
        if missing_tables:
            engine.dispose()
            pytest.fail(
                "O banco de teste não está em head; execute alembic upgrade head "
                "antes da suíte de persistência."
            )
        applied_versions = set(
            connection.execute(text("SELECT version_num FROM alembic_version"))
            .scalars()
            .all()
        )
        if applied_versions != {EXPECTED_MIGRATION}:
            engine.dispose()
            pytest.fail("A migration da Fase 12 não está aplicada em head")
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def clean_test_database(test_engine):
    table_names = ", ".join(TEST_DATA_TABLES)
    cleanup_statement = text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY")

    with test_engine.begin() as connection:
        connection.execute(cleanup_statement)
        for statement in REFERENCE_DATA_SQL:
            connection.execute(text(statement))

    yield

    with test_engine.begin() as connection:
        connection.execute(cleanup_statement)
        for statement in REFERENCE_DATA_SQL:
            connection.execute(text(statement))


@pytest.fixture
def session(test_engine, clean_test_database):
    connection = test_engine.connect()
    transaction = connection.begin()
    database_session = Session(
        bind=connection,
        # Application commits and rollbacks stay inside a savepoint. The
        # fixture-owned outer transaction is rolled back after each test.
        join_transaction_mode="create_savepoint",
    )
    try:
        yield database_session
    finally:
        database_session.close()
        transaction.rollback()
        connection.close()
