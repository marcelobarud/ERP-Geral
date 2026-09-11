import importlib.util
from pathlib import Path
from unittest.mock import Mock

MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "20260911_0008_sales_stock_integration.py"
)


def load_migration():
    spec = importlib.util.spec_from_file_location("phase6_migration", MIGRATION_PATH)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_phase6_migration_creates_sales_returns() -> None:
    migration = load_migration()
    migration.op = Mock()

    assert migration.revision == "20260911_0008"
    assert migration.down_revision == "20260911_0007"
    migration.upgrade()
    created = [call.args[0] for call in migration.op.create_table.call_args_list]
    assert created == ["devolucoes_venda", "devolucoes_venda_itens"]


def test_phase6_migration_downgrade_removes_sales_returns() -> None:
    migration = load_migration()
    migration.op = Mock()
    migration.downgrade()
    dropped = [call.args[0] for call in migration.op.drop_table.call_args_list]
    assert dropped == ["devolucoes_venda_itens", "devolucoes_venda"]
