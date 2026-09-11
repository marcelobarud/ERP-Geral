import importlib.util
from pathlib import Path
from unittest.mock import Mock

MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "20260911_0010_module_configuration.py"
)


def load_migration():
    spec = importlib.util.spec_from_file_location("phase9_migration", MIGRATION_PATH)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_phase9_migration_creates_module_configuration() -> None:
    migration = load_migration()
    migration.op = Mock()
    assert migration.revision == "20260911_0010"
    assert migration.down_revision == "20260911_0009"
    migration.upgrade()
    assert [call.args[0] for call in migration.op.create_table.call_args_list] == [
        "modulos_erp"
    ]


def test_phase9_migration_downgrade_removes_module_configuration() -> None:
    migration = load_migration()
    migration.op = Mock()
    migration.downgrade()
    assert [call.args[0] for call in migration.op.drop_table.call_args_list] == [
        "modulos_erp"
    ]
