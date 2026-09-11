"""Adiciona orcamentos e pedidos de venda."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260911_0005"
down_revision: str | None = "20260911_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _money_columns() -> list[sa.Column]:
    return [
        sa.Column("desconto", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("acrescimo", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("frete", sa.Numeric(12, 2), server_default="0", nullable=False),
    ]


def _item_columns(parent_column: str) -> list[sa.Column]:
    return [
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(parent_column, sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=False),
        sa.Column("produto_nome", sa.String(255), nullable=False),
        sa.Column("sku", sa.String(80), nullable=False),
        sa.Column("fornecedor_id", sa.Integer(), nullable=False),
        sa.Column("fornecedor_nome", sa.String(255), nullable=False),
        sa.Column("quantidade", sa.Numeric(12, 3), nullable=False),
        sa.Column("preco_unitario", sa.Numeric(12, 2), nullable=False),
        sa.Column("desconto", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("acrescimo", sa.Numeric(12, 2), server_default="0", nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "condicoes_pagamento",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("descricao", sa.String(255), nullable=True),
        sa.Column("ativo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codigo"),
    )
    conditions = sa.table(
        "condicoes_pagamento",
        sa.column("codigo", sa.String()),
        sa.column("nome", sa.String()),
        sa.column("descricao", sa.String()),
    )
    op.bulk_insert(
        conditions,
        [
            {
                "codigo": "A_VISTA",
                "nome": "À vista",
                "descricao": "Pagamento integral no ato.",
            },
            {
                "codigo": "PRAZO_30",
                "nome": "30 dias",
                "descricao": "Pagamento em 30 dias.",
            },
        ],
    )

    op.create_table(
        "orcamentos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("numero", sa.String(40), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("funcionario_id", sa.Integer(), nullable=True),
        sa.Column("condicao_pagamento_id", sa.Integer(), nullable=True),
        sa.Column("validade", sa.Date(), nullable=True),
        *_money_columns(),
        sa.Column("status", sa.String(20), server_default="RASCUNHO", nullable=False),
        sa.Column("observacao", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"]),
        sa.ForeignKeyConstraint(["funcionario_id"], ["funcionarios.id"]),
        sa.ForeignKeyConstraint(
            ["condicao_pagamento_id"], ["condicoes_pagamento.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("numero"),
        sa.CheckConstraint(
            "status IN ('RASCUNHO', 'ENVIADO', 'APROVADO', 'RECUSADO', 'EXPIRADO', 'CANCELADO')",
            name="ck_orcamentos_status_valido",
        ),
        sa.CheckConstraint("desconto >= 0", name="ck_orcamentos_desconto_nao_negativo"),
        sa.CheckConstraint("acrescimo >= 0", name="ck_orcamentos_acrescimo_nao_negativo"),
        sa.CheckConstraint("frete >= 0", name="ck_orcamentos_frete_nao_negativo"),
    )
    op.create_index("ix_orcamentos_cliente_id", "orcamentos", ["cliente_id"])
    op.create_index("ix_orcamentos_funcionario_id", "orcamentos", ["funcionario_id"])

    op.create_table(
        "orcamento_itens",
        *_item_columns("orcamento_id"),
        sa.ForeignKeyConstraint(["orcamento_id"], ["orcamentos.id"]),
        sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"]),
        sa.ForeignKeyConstraint(["fornecedor_id"], ["fornecedores.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("quantidade > 0", name="ck_orcamento_itens_quantidade_positiva"),
        sa.CheckConstraint("preco_unitario >= 0", name="ck_orcamento_itens_preco_nao_negativo"),
        sa.CheckConstraint("desconto >= 0", name="ck_orcamento_itens_desconto_nao_negativo"),
        sa.CheckConstraint("acrescimo >= 0", name="ck_orcamento_itens_acrescimo_nao_negativo"),
    )
    op.create_index("ix_orcamento_itens_orcamento_id", "orcamento_itens", ["orcamento_id"])
    op.create_index("ix_orcamento_itens_produto_id", "orcamento_itens", ["produto_id"])

    op.create_table(
        "pedidos_venda",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("numero", sa.String(40), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("funcionario_id", sa.Integer(), nullable=True),
        sa.Column("orcamento_id", sa.Integer(), nullable=True),
        sa.Column("venda_id", sa.Integer(), nullable=True),
        sa.Column("condicao_pagamento_id", sa.Integer(), nullable=True),
        *_money_columns(),
        sa.Column("status", sa.String(20), server_default="RASCUNHO", nullable=False),
        sa.Column("observacao", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"]),
        sa.ForeignKeyConstraint(["funcionario_id"], ["funcionarios.id"]),
        sa.ForeignKeyConstraint(["orcamento_id"], ["orcamentos.id"]),
        sa.ForeignKeyConstraint(["venda_id"], ["vendas.id"]),
        sa.ForeignKeyConstraint(
            ["condicao_pagamento_id"], ["condicoes_pagamento.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("numero"),
        sa.UniqueConstraint("orcamento_id", name="uq_pedido_venda_orcamento"),
        sa.UniqueConstraint("venda_id", name="uq_pedido_venda_venda"),
        sa.CheckConstraint(
            "status IN ('RASCUNHO', 'CONFIRMADO', 'CONCLUIDO', 'CANCELADO')",
            name="ck_pedidos_venda_status_valido",
        ),
        sa.CheckConstraint("desconto >= 0", name="ck_pedidos_venda_desconto_nao_negativo"),
        sa.CheckConstraint("acrescimo >= 0", name="ck_pedidos_venda_acrescimo_nao_negativo"),
        sa.CheckConstraint("frete >= 0", name="ck_pedidos_venda_frete_nao_negativo"),
    )
    op.create_index("ix_pedidos_venda_cliente_id", "pedidos_venda", ["cliente_id"])
    op.create_index("ix_pedidos_venda_funcionario_id", "pedidos_venda", ["funcionario_id"])
    op.create_index("ix_pedidos_venda_orcamento_id", "pedidos_venda", ["orcamento_id"])
    op.create_index("ix_pedidos_venda_venda_id", "pedidos_venda", ["venda_id"])

    op.create_table(
        "pedido_venda_itens",
        *_item_columns("pedido_id"),
        sa.ForeignKeyConstraint(["pedido_id"], ["pedidos_venda.id"]),
        sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"]),
        sa.ForeignKeyConstraint(["fornecedor_id"], ["fornecedores.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("quantidade > 0", name="ck_pedido_itens_quantidade_positiva"),
        sa.CheckConstraint("preco_unitario >= 0", name="ck_pedido_itens_preco_nao_negativo"),
        sa.CheckConstraint("desconto >= 0", name="ck_pedido_itens_desconto_nao_negativo"),
        sa.CheckConstraint("acrescimo >= 0", name="ck_pedido_itens_acrescimo_nao_negativo"),
    )
    op.create_index("ix_pedido_venda_itens_pedido_id", "pedido_venda_itens", ["pedido_id"])
    op.create_index("ix_pedido_venda_itens_produto_id", "pedido_venda_itens", ["produto_id"])


def downgrade() -> None:
    op.drop_index("ix_pedido_venda_itens_produto_id", table_name="pedido_venda_itens")
    op.drop_index("ix_pedido_venda_itens_pedido_id", table_name="pedido_venda_itens")
    op.drop_table("pedido_venda_itens")
    op.drop_index("ix_pedidos_venda_venda_id", table_name="pedidos_venda")
    op.drop_index("ix_pedidos_venda_orcamento_id", table_name="pedidos_venda")
    op.drop_index("ix_pedidos_venda_funcionario_id", table_name="pedidos_venda")
    op.drop_index("ix_pedidos_venda_cliente_id", table_name="pedidos_venda")
    op.drop_table("pedidos_venda")
    op.drop_index("ix_orcamento_itens_produto_id", table_name="orcamento_itens")
    op.drop_index("ix_orcamento_itens_orcamento_id", table_name="orcamento_itens")
    op.drop_table("orcamento_itens")
    op.drop_index("ix_orcamentos_funcionario_id", table_name="orcamentos")
    op.drop_index("ix_orcamentos_cliente_id", table_name="orcamentos")
    op.drop_table("orcamentos")
    op.drop_table("condicoes_pagamento")
