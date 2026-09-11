import importlib.util
from pathlib import Path
from unittest.mock import Mock

MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "20260911_0007_purchases_receipts.py"
)


def load_migration():
    spec = importlib.util.spec_from_file_location("phase5_migration", MIGRATION_PATH)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_phase5_migration_creates_purchases_and_receipts() -> None:
    migration = load_migration()
    migration.op = Mock()

    assert migration.revision == "20260911_0007"
    assert migration.down_revision == "20260911_0006"
    migration.upgrade()

    created = [call.args[0] for call in migration.op.create_table.call_args_list]
    assert created == [
        "pedidos_compra",
        "pedido_compra_itens",
        "recebimentos_compra",
        "recebimentos_compra_itens",
    ]


def test_phase5_migration_downgrade_removes_purchase_tables() -> None:
    migration = load_migration()
    migration.op = Mock()

    migration.downgrade()

    dropped = [call.args[0] for call in migration.op.drop_table.call_args_list]
    assert dropped == [
        "recebimentos_compra_itens",
        "recebimentos_compra",
        "pedido_compra_itens",
        "pedidos_compra",
    ]
