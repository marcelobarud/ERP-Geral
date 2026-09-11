import importlib.util
from pathlib import Path
from unittest.mock import Mock

MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "20260911_0006_inventory_foundation.py"
)


def load_migration():
    spec = importlib.util.spec_from_file_location("phase4_migration", MIGRATION_PATH)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_phase4_migration_creates_inventory_foundation() -> None:
    migration = load_migration()
    migration.op = Mock()

    assert migration.revision == "20260911_0006"
    assert migration.down_revision == "20260911_0005"
    migration.upgrade()

    created = [call.args[0] for call in migration.op.create_table.call_args_list]
    assert created == [
        "depositos_estoque",
        "configuracoes_estoque",
        "movimentacoes_estoque",
        "inventarios_estoque",
        "inventarios_estoque_itens",
    ]


def test_phase4_migration_downgrade_removes_inventory_foundation() -> None:
    migration = load_migration()
    migration.op = Mock()

    migration.downgrade()

    dropped = [call.args[0] for call in migration.op.drop_table.call_args_list]
    assert dropped == [
        "inventarios_estoque_itens",
        "inventarios_estoque",
        "movimentacoes_estoque",
        "configuracoes_estoque",
        "depositos_estoque",
    ]
