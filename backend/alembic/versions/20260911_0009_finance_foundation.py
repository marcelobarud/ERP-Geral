"""Adiciona financeiro operacional."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260911_0009"
down_revision: str | None = "20260911_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categorias_financeiras",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("tipo", sa.String(10), nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )
    op.create_table(
        "contas_financeiras",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("saldo_inicial", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )
    contas = sa.table("contas_financeiras", sa.column("nome", sa.String()))
    op.bulk_insert(contas, [{"nome": "Caixa principal"}])
    op.create_table(
        "titulos_financeiros",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("numero", sa.String(60), nullable=False),
        sa.Column("tipo", sa.String(10), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=True),
        sa.Column("fornecedor_id", sa.Integer(), nullable=True),
        sa.Column("categoria_id", sa.Integer(), nullable=True),
        sa.Column("origem_tipo", sa.String(40), nullable=True),
        sa.Column("origem_id", sa.Integer(), nullable=True),
        sa.Column("valor_original", sa.Numeric(12, 2), nullable=False),
        sa.Column("descricao", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"]),
        sa.ForeignKeyConstraint(["fornecedor_id"], ["fornecedores.id"]),
        sa.ForeignKeyConstraint(["categoria_id"], ["categorias_financeiras.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("numero"),
        sa.CheckConstraint("tipo IN ('RECEBER', 'PAGAR')", name="ck_titulos_financeiros_tipo_valido"),
        sa.CheckConstraint("valor_original >= 0", name="ck_titulos_financeiros_valor_nao_negativo"),
    )
    op.create_index("ix_titulos_financeiros_cliente_id", "titulos_financeiros", ["cliente_id"])
    op.create_index("ix_titulos_financeiros_fornecedor_id", "titulos_financeiros", ["fornecedor_id"])
    op.create_table(
        "parcelas_financeiras",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("titulo_id", sa.Integer(), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("vencimento", sa.Date(), nullable=False),
        sa.Column("valor", sa.Numeric(12, 2), nullable=False),
        sa.ForeignKeyConstraint(["titulo_id"], ["titulos_financeiros.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("valor >= 0", name="ck_parcelas_financeiras_valor_nao_negativo"),
        sa.CheckConstraint("numero > 0", name="ck_parcelas_financeiras_numero_positivo"),
    )
    op.create_index("ix_parcelas_financeiras_titulo_id", "parcelas_financeiras", ["titulo_id"])
    op.create_table(
        "liquidacoes_financeiras",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("parcela_id", sa.Integer(), nullable=False),
        sa.Column("conta_id", sa.Integer(), nullable=False),
        sa.Column("valor", sa.Numeric(12, 2), nullable=False),
        sa.Column("data_liquidacao", sa.Date(), nullable=False),
        sa.Column("status", sa.String(12), server_default="CONFIRMADA", nullable=False),
        sa.Column("observacao", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["parcela_id"], ["parcelas_financeiras.id"]),
        sa.ForeignKeyConstraint(["conta_id"], ["contas_financeiras.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("valor > 0", name="ck_liquidacoes_financeiras_valor_positivo"),
        sa.CheckConstraint("status IN ('CONFIRMADA', 'ESTORNADA')", name="ck_liquidacoes_financeiras_status_valido"),
    )
    op.create_index("ix_liquidacoes_financeiras_parcela_id", "liquidacoes_financeiras", ["parcela_id"])


def downgrade() -> None:
    op.drop_index("ix_liquidacoes_financeiras_parcela_id", table_name="liquidacoes_financeiras")
    op.drop_table("liquidacoes_financeiras")
    op.drop_index("ix_parcelas_financeiras_titulo_id", table_name="parcelas_financeiras")
    op.drop_table("parcelas_financeiras")
    op.drop_index("ix_titulos_financeiros_fornecedor_id", table_name="titulos_financeiros")
    op.drop_index("ix_titulos_financeiros_cliente_id", table_name="titulos_financeiros")
    op.drop_table("titulos_financeiros")
    op.drop_table("contas_financeiras")
    op.drop_table("categorias_financeiras")
