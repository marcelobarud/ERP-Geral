"""Adiciona configuração de módulos do ERP."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260911_0010"
down_revision: str | None = "20260911_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


MODULES = (
    ("commercial", "Comercial", 10),
    ("purchases", "Compras", 20),
    ("inventory", "Estoque", 30),
    ("finance", "Financeiro", 40),
    ("reports", "Relatórios", 50),
)


def upgrade() -> None:
    op.create_table(
        "modulos_erp",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("ordem", sa.Integer(), server_default="0", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codigo"),
    )
    table = sa.table(
        "modulos_erp",
        sa.column("codigo", sa.String()),
        sa.column("nome", sa.String()),
        sa.column("ordem", sa.Integer()),
    )
    op.bulk_insert(
        table,
        [{"codigo": code, "nome": name, "ordem": order} for code, name, order in MODULES],
    )


def downgrade() -> None:
    op.drop_table("modulos_erp")
