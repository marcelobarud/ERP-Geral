"""Adiciona depósitos, movimentações e inventário."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260911_0006"
down_revision: str | None = "20260911_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "depositos_estoque",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("padrao", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codigo"),
    )
    op.create_index(
        "uq_depositos_estoque_padrao",
        "depositos_estoque",
        ["padrao"],
        unique=True,
        postgresql_where=sa.text("padrao = true"),
    )
    op.execute(
        sa.text(
            "INSERT INTO depositos_estoque "
            "(codigo, nome, padrao, created_at, updated_at) "
            "VALUES ('PRINCIPAL', 'Depósito principal', TRUE, "
            "CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        )
    )

    op.create_table(
        "configuracoes_estoque",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "permitir_saldo_negativo",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        sa.text(
            "INSERT INTO configuracoes_estoque "
            "(id, permitir_saldo_negativo, updated_at) "
            "VALUES (1, FALSE, CURRENT_TIMESTAMP)"
        )
    )

    op.create_table(
        "movimentacoes_estoque",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=False),
        sa.Column("deposito_id", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(24), nullable=False),
        sa.Column("quantidade", sa.Numeric(12, 3), nullable=False),
        sa.Column("data_movimentacao", sa.DateTime(timezone=True), nullable=False),
        sa.Column("origem", sa.String(40), nullable=False),
        sa.Column("documento_tipo", sa.String(40), nullable=True),
        sa.Column("documento_id", sa.Integer(), nullable=True),
        sa.Column("movimento_origem_id", sa.Integer(), nullable=True),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("observacao", sa.String(500), nullable=True),
        sa.Column("chave_idempotencia", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"]),
        sa.ForeignKeyConstraint(["deposito_id"], ["depositos_estoque.id"]),
        sa.ForeignKeyConstraint(
            ["movimento_origem_id"], ["movimentacoes_estoque.id"]
        ),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chave_idempotencia", name="uq_movimentacoes_estoque_idempotencia"),
        sa.CheckConstraint(
            "tipo IN ('ENTRADA', 'SAIDA', 'AJUSTE_ENTRADA', 'AJUSTE_SAIDA', "
            "'DEVOLUCAO_ENTRADA', 'DEVOLUCAO_SAIDA', 'REVERSAO')",
            name="ck_movimentacoes_estoque_tipo_valido",
        ),
        sa.CheckConstraint(
            "quantidade > 0", name="ck_movimentacoes_estoque_quantidade_positiva"
        ),
    )
    op.create_index(
        "ix_movimentacoes_estoque_produto_id",
        "movimentacoes_estoque",
        ["produto_id"],
    )
    op.create_index(
        "ix_movimentacoes_estoque_deposito_id",
        "movimentacoes_estoque",
        ["deposito_id"],
    )

    op.create_table(
        "inventarios_estoque",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("deposito_id", sa.Integer(), nullable=False),
        sa.Column("data_inventario", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), server_default="RASCUNHO", nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("observacao", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["deposito_id"], ["depositos_estoque.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('RASCUNHO', 'CONFIRMADO', 'CANCELADO')",
            name="ck_inventarios_estoque_status_valido",
        ),
    )
    op.create_index(
        "ix_inventarios_estoque_deposito_id", "inventarios_estoque", ["deposito_id"]
    )

    op.create_table(
        "inventarios_estoque_itens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("inventario_id", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=False),
        sa.Column("saldo_sistema", sa.Numeric(12, 3), nullable=False),
        sa.Column("quantidade_contada", sa.Numeric(12, 3), nullable=False),
        sa.Column("diferenca", sa.Numeric(12, 3), nullable=False),
        sa.ForeignKeyConstraint(["inventario_id"], ["inventarios_estoque.id"]),
        sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "inventario_id", "produto_id", name="uq_inventario_estoque_produto"
        ),
        sa.CheckConstraint(
            "quantidade_contada >= 0",
            name="ck_inventarios_estoque_quantidade_contada_nao_negativa",
        ),
    )
    op.create_index(
        "ix_inventarios_estoque_itens_inventario_id",
        "inventarios_estoque_itens",
        ["inventario_id"],
    )
    op.create_index(
        "ix_inventarios_estoque_itens_produto_id",
        "inventarios_estoque_itens",
        ["produto_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_inventarios_estoque_itens_produto_id",
        table_name="inventarios_estoque_itens",
    )
    op.drop_index(
        "ix_inventarios_estoque_itens_inventario_id",
        table_name="inventarios_estoque_itens",
    )
    op.drop_table("inventarios_estoque_itens")
    op.drop_index("ix_inventarios_estoque_deposito_id", table_name="inventarios_estoque")
    op.drop_table("inventarios_estoque")
    op.drop_index(
        "ix_movimentacoes_estoque_deposito_id", table_name="movimentacoes_estoque"
    )
    op.drop_index(
        "ix_movimentacoes_estoque_produto_id", table_name="movimentacoes_estoque"
    )
    op.drop_table("movimentacoes_estoque")
    op.drop_table("configuracoes_estoque")
    op.drop_index("uq_depositos_estoque_padrao", table_name="depositos_estoque")
    op.drop_table("depositos_estoque")
