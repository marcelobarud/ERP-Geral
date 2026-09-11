"""Preserva origem comercial e condição de pagamento na venda."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260911_0011"
down_revision: str | None = "20260911_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("vendas", sa.Column("pedido_venda_id", sa.Integer(), nullable=True))
    op.add_column("vendas", sa.Column("condicao_pagamento_id", sa.Integer(), nullable=True))
    op.create_index("ix_vendas_pedido_venda_id", "vendas", ["pedido_venda_id"], unique=True)
    op.create_index("ix_vendas_condicao_pagamento_id", "vendas", ["condicao_pagamento_id"])
    op.create_foreign_key("fk_vendas_pedido_venda_id", "vendas", "pedidos_venda", ["pedido_venda_id"], ["id"])
    op.create_foreign_key("fk_vendas_condicao_pagamento_id", "vendas", "condicoes_pagamento", ["condicao_pagamento_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_vendas_condicao_pagamento_id", "vendas", type_="foreignkey")
    op.drop_constraint("fk_vendas_pedido_venda_id", "vendas", type_="foreignkey")
    op.drop_index("ix_vendas_condicao_pagamento_id", table_name="vendas")
    op.drop_index("ix_vendas_pedido_venda_id", table_name="vendas")
    op.drop_column("vendas", "condicao_pagamento_id")
    op.drop_column("vendas", "pedido_venda_id")
