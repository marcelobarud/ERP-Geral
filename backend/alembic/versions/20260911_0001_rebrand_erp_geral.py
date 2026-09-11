"""Atualiza o branding padrão legado para ERP Geral."""

import sqlalchemy as sa

from alembic import op

revision = "20260911_0001"
down_revision = "20260823_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE configuracoes_aparencia
            SET nome_sistema = 'ERP Geral'
            WHERE nome_sistema = 'CRM Geral'
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE configuracoes_aparencia
            SET nome_sistema = 'CRM Geral'
            WHERE nome_sistema = 'ERP Geral'
            """
        )
    )
