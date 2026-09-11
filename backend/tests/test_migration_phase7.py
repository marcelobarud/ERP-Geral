import importlib.util
from pathlib import Path
from unittest.mock import Mock

MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "20260911_0009_finance_foundation.py"
)


def load_migration():
    spec = importlib.util.spec_from_file_location("phase7_migration", MIGRATION_PATH)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_phase7_migration_creates_finance_foundation() -> None:
    migration = load_migration()
    migration.op = Mock()
    assert migration.revision == "20260911_0009"
    assert migration.down_revision == "20260911_0008"
    migration.upgrade()
    created = [call.args[0] for call in migration.op.create_table.call_args_list]
    assert created == [
        "categorias_financeiras",
        "contas_financeiras",
        "titulos_financeiros",
        "parcelas_financeiras",
        "liquidacoes_financeiras",
    ]


def test_phase7_migration_downgrade_removes_finance_foundation() -> None:
    migration = load_migration()
    migration.op = Mock()
    migration.downgrade()
    dropped = [call.args[0] for call in migration.op.drop_table.call_args_list]
    assert dropped == [
        "liquidacoes_financeiras",
        "parcelas_financeiras",
        "titulos_financeiros",
        "contas_financeiras",
        "categorias_financeiras",
    ]
