import importlib.util
from pathlib import Path
from unittest.mock import Mock

import sqlalchemy as sa

MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "20260911_0002_erp_foundation.py"
)


def load_migration():
    spec = importlib.util.spec_from_file_location("phase0_migration", MIGRATION_PATH)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_phase0_migration_revision_chain_and_operational_columns() -> None:
    migration = load_migration()

    assert migration.revision == "20260911_0002"
    assert migration.down_revision == "20260911_0001"
    assert len(migration.revision) <= 32

    migration.op = Mock()
    migration.upgrade()

    assert migration.op.add_column.call_count == 16
    added_columns = [call.args for call in migration.op.add_column.call_args_list]
    assert ("vendas",) == added_columns[8][:1]
    assert any(args[1].name == "status" for args in added_columns)
    assert any(args[1].name == "observacao" for args in added_columns)
    migration.op.create_check_constraint.assert_called_once_with(
        "ck_vendas_status_valido",
        "vendas",
        "status IN ('CONCLUIDA', 'CANCELADA')",
    )

    timestamp_updates = [
        call.args[0].text
        for call in migration.op.execute.call_args_list
        if isinstance(call.args[0], sa.sql.elements.TextClause)
    ]
    assert len(timestamp_updates) == 6


def test_phase0_migration_downgrade_removes_new_columns() -> None:
    migration = load_migration()
    migration.op = Mock()

    migration.downgrade()

    migration.op.drop_constraint.assert_called_once_with(
        "ck_vendas_status_valido", "vendas", type_="check"
    )
    assert migration.op.drop_column.call_count == 16
