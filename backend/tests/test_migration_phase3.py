import importlib.util
from pathlib import Path
from unittest.mock import Mock

MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "20260911_0005_commercial_documents.py"
)


def load_migration():
    spec = importlib.util.spec_from_file_location("phase3_migration", MIGRATION_PATH)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_phase3_migration_creates_commercial_documents() -> None:
    migration = load_migration()
    migration.op = Mock()

    assert migration.revision == "20260911_0005"
    assert migration.down_revision == "20260911_0004"
    migration.upgrade()

    created = [call.args[0] for call in migration.op.create_table.call_args_list]
    assert created == [
        "condicoes_pagamento",
        "orcamentos",
        "orcamento_itens",
        "pedidos_venda",
        "pedido_venda_itens",
    ]


def test_phase3_migration_downgrade_removes_commercial_documents() -> None:
    migration = load_migration()
    migration.op = Mock()

    migration.downgrade()

    dropped = [call.args[0] for call in migration.op.drop_table.call_args_list]
    assert dropped == [
        "pedido_venda_itens",
        "pedidos_venda",
        "orcamento_itens",
        "orcamentos",
        "condicoes_pagamento",
    ]
