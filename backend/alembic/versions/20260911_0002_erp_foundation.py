"""Prepara ciclo transacional, timestamps e observacoes da Fase 0."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260911_0002"
down_revision: str | None = "20260911_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


TIMESTAMP_TABLES = (
    "clientes",
    "fornecedores",
    "funcionarios",
    "produtos",
    "vendas",
    "venda_itens",
)


def _add_timestamps(table_name: str) -> None:
    op.add_column(
        table_name,
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.add_column(
        table_name,
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.execute(
        sa.text(
            f"UPDATE {table_name} "
            "SET created_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP "
            "WHERE created_at IS NULL OR updated_at IS NULL"
        )
    )
    op.alter_column(
        table_name,
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
    op.alter_column(
        table_name,
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )


def upgrade() -> None:
    for table_name in TIMESTAMP_TABLES:
        _add_timestamps(table_name)

    op.add_column(
        "vendas",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="CONCLUIDA",
        ),
    )
    op.add_column(
        "vendas",
        sa.Column("cancelada_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "vendas",
        sa.Column("motivo_cancelamento", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "vendas",
        sa.Column("observacao", sa.String(length=1000), nullable=True),
    )
    op.create_check_constraint(
        "ck_vendas_status_valido",
        "vendas",
        "status IN ('CONCLUIDA', 'CANCELADA')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_vendas_status_valido", "vendas", type_="check")
    op.drop_column("vendas", "observacao")
    op.drop_column("vendas", "motivo_cancelamento")
    op.drop_column("vendas", "cancelada_em")
    op.drop_column("vendas", "status")

    for table_name in reversed(TIMESTAMP_TABLES):
        op.drop_column(table_name, "updated_at")
        op.drop_column(table_name, "created_at")
