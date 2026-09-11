"""Adiciona usuarios, sessoes e trilha de auditoria."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260911_0003"
down_revision: str | None = "20260911_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "role",
            sa.String(length=20),
            server_default="OPERATOR",
            nullable=False,
        ),
        sa.Column("funcionario_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["funcionario_id"], ["funcionarios.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_usuarios_email"),
        sa.UniqueConstraint("funcionario_id"),
        sa.CheckConstraint(
            "role IN ('ADMIN', 'MANAGER', 'OPERATOR')",
            name="ck_usuarios_role_valido",
        ),
    )
    op.create_index("ix_usuarios_email", "usuarios", ["email"], unique=False)

    op.create_table(
        "sessoes_autenticacao",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        "ix_sessoes_autenticacao_usuario_id",
        "sessoes_autenticacao",
        ["usuario_id"],
        unique=False,
    )
    op.create_index(
        "ix_sessoes_autenticacao_token_hash",
        "sessoes_autenticacao",
        ["token_hash"],
        unique=True,
    )

    op.create_table(
        "logs_auditoria",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("acao", sa.String(length=80), nullable=False),
        sa.Column("entidade", sa.String(length=80), nullable=False),
        sa.Column("entidade_id", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_logs_auditoria_usuario_id", "logs_auditoria", ["usuario_id"])
    op.create_index("ix_logs_auditoria_acao", "logs_auditoria", ["acao"])
    op.create_index("ix_logs_auditoria_entidade", "logs_auditoria", ["entidade"])


def downgrade() -> None:
    op.drop_index("ix_logs_auditoria_entidade", table_name="logs_auditoria")
    op.drop_index("ix_logs_auditoria_acao", table_name="logs_auditoria")
    op.drop_index("ix_logs_auditoria_usuario_id", table_name="logs_auditoria")
    op.drop_table("logs_auditoria")
    op.drop_index(
        "ix_sessoes_autenticacao_token_hash", table_name="sessoes_autenticacao"
    )
    op.drop_index(
        "ix_sessoes_autenticacao_usuario_id", table_name="sessoes_autenticacao"
    )
    op.drop_table("sessoes_autenticacao")
    op.drop_index("ix_usuarios_email", table_name="usuarios")
    op.drop_table("usuarios")
