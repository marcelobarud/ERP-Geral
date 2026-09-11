import importlib.util
from pathlib import Path
from unittest.mock import Mock

MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "20260911_0001_rebrand_erp_geral.py"
)


def load_migration():
    spec = importlib.util.spec_from_file_location(
        "rebrand_erp_geral_migration", MIGRATION_PATH
    )
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_rebrand_migration_updates_only_legacy_default() -> None:
    migration = load_migration()
    migration.op = Mock()

    migration.upgrade()

    statement = str(migration.op.execute.call_args.args[0])
    assert "SET nome_sistema = 'ERP Geral'" in statement
    assert "WHERE nome_sistema = 'CRM Geral'" in statement


def test_rebrand_migration_downgrade_targets_only_new_default() -> None:
    migration = load_migration()
    migration.op = Mock()

    migration.downgrade()

    statement = str(migration.op.execute.call_args.args[0])
    assert "SET nome_sistema = 'CRM Geral'" in statement
    assert "WHERE nome_sistema = 'ERP Geral'" in statement
