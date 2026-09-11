"""Adiciona devoluções de venda para integração com estoque."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260911_0008"
down_revision: str | None = "20260911_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "devolucoes_venda",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("venda_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), server_default="RASCUNHO", nullable=False),
        sa.Column("motivo", sa.String(500), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["venda_id"], ["vendas.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('RASCUNHO', 'APROVADA', 'CANCELADA')",
            name="ck_devolucoes_venda_status_valido",
        ),
    )
    op.create_index("ix_devolucoes_venda_venda_id", "devolucoes_venda", ["venda_id"])
    op.create_table(
        "devolucoes_venda_itens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("devolucao_id", sa.Integer(), nullable=False),
        sa.Column("venda_item_id", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=False),
        sa.Column("produto_nome", sa.String(255), nullable=False),
        sa.Column("quantidade", sa.Numeric(12, 3), nullable=False),
        sa.Column("preco_unitario", sa.Numeric(12, 2), nullable=False),
        sa.ForeignKeyConstraint(["devolucao_id"], ["devolucoes_venda.id"]),
        sa.ForeignKeyConstraint(["venda_item_id"], ["venda_itens.id"]),
        sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("quantidade > 0", name="ck_devolucao_quantidade_positiva"),
    )
    op.create_index(
        "ix_devolucoes_venda_itens_devolucao_id",
        "devolucoes_venda_itens",
        ["devolucao_id"],
    )
    op.create_index(
        "ix_devolucoes_venda_itens_venda_item_id",
        "devolucoes_venda_itens",
        ["venda_item_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_devolucoes_venda_itens_venda_item_id",
        table_name="devolucoes_venda_itens",
    )
    op.drop_index(
        "ix_devolucoes_venda_itens_devolucao_id",
        table_name="devolucoes_venda_itens",
    )
    op.drop_table("devolucoes_venda_itens")
    op.drop_index("ix_devolucoes_venda_venda_id", table_name="devolucoes_venda")
    op.drop_table("devolucoes_venda")
