import importlib.util
from pathlib import Path
from unittest.mock import Mock

MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "20260911_0012_report_page_ids.py"
)


def load_migration():
    spec = importlib.util.spec_from_file_location("phase14_migration", MIGRATION_PATH)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_phase14_migration_recreates_page_constraint() -> None:
    migration = load_migration()
    migration.op = Mock()

    migration.upgrade()

    migration.op.drop_constraint.assert_called_once_with(
        "ck_config_aparencia_paginas_pagina",
        "configuracoes_aparencia_paginas",
        type_="check",
    )
    migration.op.create_check_constraint.assert_called_once()
    assert "reports_finance" in migration.op.create_check_constraint.call_args.args[2]


def test_phase14_migration_downgrade_restores_original_constraint() -> None:
    migration = load_migration()
    migration.op = Mock()

    migration.downgrade()

    expression = migration.op.create_check_constraint.call_args.args[2]
    assert "reports_finance" not in expression
    assert "settings" in expression
