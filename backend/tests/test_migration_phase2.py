import importlib.util
from pathlib import Path
from unittest.mock import Mock

MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "20260911_0004_catalog_foundation.py"
)


def load_migration():
    spec = importlib.util.spec_from_file_location("phase2_migration", MIGRATION_PATH)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_phase2_migration_preserves_legacy_catalog_and_adds_foundation() -> None:
    migration = load_migration()
    migration.op = Mock()

    assert migration.revision == "20260911_0004"
    assert migration.down_revision == "20260911_0003"
    migration.upgrade()

    created = [call.args[0] for call in migration.op.create_table.call_args_list]
    assert created == [
        "unidades_medida",
        "categorias_produto",
        "produtos_fornecedores",
        "historicos_custo_produto",
    ]
    assert migration.op.add_column.call_count == 6
    assert migration.op.create_index.call_count == 4


def test_phase2_migration_downgrade_removes_only_catalog_additions() -> None:
    migration = load_migration()
    migration.op = Mock()

    migration.downgrade()

    dropped = [call.args[0] for call in migration.op.drop_table.call_args_list]
    assert dropped == [
        "historicos_custo_produto",
        "produtos_fornecedores",
        "categorias_produto",
        "unidades_medida",
    ]
    assert migration.op.drop_column.call_count == 6
