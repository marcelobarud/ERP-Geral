import importlib.util
from pathlib import Path
from unittest.mock import Mock

MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "20260911_0003_security_audit.py"
)


def load_migration():
    spec = importlib.util.spec_from_file_location("phase1_migration", MIGRATION_PATH)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_phase1_migration_revision_and_security_tables() -> None:
    migration = load_migration()
    migration.op = Mock()

    assert migration.revision == "20260911_0003"
    assert migration.down_revision == "20260911_0002"
    migration.upgrade()

    tables = [call.args[0] for call in migration.op.create_table.call_args_list]
    assert tables == [
        "usuarios",
        "sessoes_autenticacao",
        "logs_auditoria",
    ]
    assert migration.op.create_index.call_count == 6


def test_phase1_migration_downgrade_is_reversible() -> None:
    migration = load_migration()
    migration.op = Mock()

    migration.downgrade()

    assert migration.op.drop_table.call_args_list[0].args == ("logs_auditoria",)
    assert migration.op.drop_table.call_args_list[-1].args == ("usuarios",)
