"""Adiciona pedidos de compra e recebimentos."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260911_0007"
down_revision: str | None = "20260911_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pedidos_compra",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("numero", sa.String(40), nullable=False),
        sa.Column("fornecedor_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(24), server_default="RASCUNHO", nullable=False),
        sa.Column("previsao_entrega", sa.Date(), nullable=True),
        sa.Column("observacao", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["fornecedor_id"], ["fornecedores.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("numero"),
        sa.CheckConstraint(
            "status IN ('RASCUNHO', 'EMITIDO', 'PARCIALMENTE_RECEBIDO', 'RECEBIDO', 'CANCELADO')",
            name="ck_pedidos_compra_status_valido",
        ),
    )
    op.create_index("ix_pedidos_compra_fornecedor_id", "pedidos_compra", ["fornecedor_id"])

    op.create_table(
        "pedido_compra_itens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pedido_id", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=False),
        sa.Column("produto_nome", sa.String(255), nullable=False),
        sa.Column("sku", sa.String(80), nullable=False),
        sa.Column("quantidade", sa.Numeric(12, 3), nullable=False),
        sa.Column("quantidade_recebida", sa.Numeric(12, 3), server_default="0", nullable=False),
        sa.Column("custo_unitario", sa.Numeric(12, 2), nullable=False),
        sa.ForeignKeyConstraint(["pedido_id"], ["pedidos_compra.id"]),
        sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("quantidade > 0", name="ck_pedido_compra_quantidade_positiva"),
        sa.CheckConstraint("custo_unitario >= 0", name="ck_pedido_compra_custo_nao_negativo"),
        sa.CheckConstraint("quantidade_recebida >= 0", name="ck_pedido_compra_recebida_nao_negativa"),
    )
    op.create_index("ix_pedido_compra_itens_pedido_id", "pedido_compra_itens", ["pedido_id"])
    op.create_index("ix_pedido_compra_itens_produto_id", "pedido_compra_itens", ["produto_id"])

    op.create_table(
        "recebimentos_compra",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pedido_id", sa.Integer(), nullable=False),
        sa.Column("data_recebimento", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), server_default="RASCUNHO", nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("observacao", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["pedido_id"], ["pedidos_compra.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('RASCUNHO', 'CONFIRMADO', 'CANCELADO')",
            name="ck_recebimentos_compra_status_valido",
        ),
    )
    op.create_index("ix_recebimentos_compra_pedido_id", "recebimentos_compra", ["pedido_id"])

    op.create_table(
        "recebimentos_compra_itens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recebimento_id", sa.Integer(), nullable=False),
        sa.Column("pedido_item_id", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=False),
        sa.Column("quantidade", sa.Numeric(12, 3), nullable=False),
        sa.Column("custo_efetivo", sa.Numeric(12, 2), nullable=False),
        sa.ForeignKeyConstraint(["recebimento_id"], ["recebimentos_compra.id"]),
        sa.ForeignKeyConstraint(["pedido_item_id"], ["pedido_compra_itens.id"]),
        sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("quantidade > 0", name="ck_recebimento_quantidade_positiva"),
        sa.CheckConstraint("custo_efetivo >= 0", name="ck_recebimento_custo_nao_negativo"),
    )
    op.create_index(
        "ix_recebimentos_compra_itens_recebimento_id",
        "recebimentos_compra_itens",
        ["recebimento_id"],
    )
    op.create_index(
        "ix_recebimentos_compra_itens_pedido_item_id",
        "recebimentos_compra_itens",
        ["pedido_item_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_recebimentos_compra_itens_pedido_item_id",
        table_name="recebimentos_compra_itens",
    )
    op.drop_index(
        "ix_recebimentos_compra_itens_recebimento_id",
        table_name="recebimentos_compra_itens",
    )
    op.drop_table("recebimentos_compra_itens")
    op.drop_index("ix_recebimentos_compra_pedido_id", table_name="recebimentos_compra")
    op.drop_table("recebimentos_compra")
    op.drop_index("ix_pedido_compra_itens_produto_id", table_name="pedido_compra_itens")
    op.drop_index("ix_pedido_compra_itens_pedido_id", table_name="pedido_compra_itens")
    op.drop_table("pedido_compra_itens")
    op.drop_index("ix_pedidos_compra_fornecedor_id", table_name="pedidos_compra")
    op.drop_table("pedidos_compra")
