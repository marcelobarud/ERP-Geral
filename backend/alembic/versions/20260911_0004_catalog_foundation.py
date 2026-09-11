"""Expande o catalogo de produtos para a fundacao ERP."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260911_0004"
down_revision: str | None = "20260911_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UNITS = (
    ("UN", "Unidade"),
    ("KG", "Quilograma"),
    ("G", "Grama"),
    ("L", "Litro"),
    ("ML", "Mililitro"),
    ("M", "Metro"),
    ("M2", "Metro quadrado"),
    ("CX", "Caixa"),
)


def upgrade() -> None:
    op.create_table(
        "unidades_medida",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("codigo", sa.String(length=10), nullable=False),
        sa.Column("nome", sa.String(length=80), nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codigo"),
    )
    units_table = sa.table(
        "unidades_medida",
        sa.column("codigo", sa.String()),
        sa.column("nome", sa.String()),
    )
    op.bulk_insert(
        units_table,
        [{"codigo": code, "nome": name} for code, name in UNITS],
    )

    op.create_table(
        "categorias_produto",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )
    op.execute(
        sa.text(
            "INSERT INTO categorias_produto "
            "(nome, ativo, created_at, updated_at) "
            "SELECT DISTINCT categoria, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP "
            "FROM produtos"
        )
    )

    op.add_column("produtos", sa.Column("sku", sa.String(80), nullable=True))
    op.add_column(
        "produtos", sa.Column("codigo_barras", sa.String(80), nullable=True)
    )
    op.add_column(
        "produtos", sa.Column("categoria_id", sa.Integer(), nullable=True)
    )
    op.add_column(
        "produtos",
        sa.Column(
            "unidade_medida",
            sa.String(10),
            server_default="UN",
            nullable=True,
        ),
    )
    op.add_column(
        "produtos",
        sa.Column("ativo", sa.Boolean(), server_default=sa.true(), nullable=True),
    )
    op.add_column(
        "produtos",
        sa.Column(
            "estoque_minimo",
            sa.Numeric(12, 3),
            server_default="0",
            nullable=True,
        ),
    )
    op.execute(
        sa.text(
            "UPDATE produtos SET sku = 'ERP-' || LPAD(id::text, 6, '0'), "
            "unidade_medida = 'UN', ativo = TRUE, estoque_minimo = 0 "
            "WHERE sku IS NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE produtos p SET categoria_id = c.id "
            "FROM categorias_produto c WHERE c.nome = p.categoria"
        )
    )
    op.alter_column("produtos", "sku", existing_type=sa.String(80), nullable=False)
    op.alter_column(
        "produtos", "unidade_medida", existing_type=sa.String(10), nullable=False
    )
    op.alter_column(
        "produtos", "ativo", existing_type=sa.Boolean(), nullable=False
    )
    op.alter_column(
        "produtos", "estoque_minimo", existing_type=sa.Numeric(12, 3), nullable=False
    )
    op.create_unique_constraint("uq_produtos_sku", "produtos", ["sku"])
    op.create_unique_constraint(
        "uq_produtos_codigo_barras", "produtos", ["codigo_barras"]
    )
    op.create_foreign_key(
        "fk_produtos_categoria_id",
        "produtos",
        "categorias_produto",
        ["categoria_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_produtos_unidade_medida",
        "produtos",
        "unidades_medida",
        ["unidade_medida"],
        ["codigo"],
    )
    op.create_check_constraint(
        "ck_produtos_estoque_minimo_nao_negativo",
        "produtos",
        "estoque_minimo >= 0",
    )

    op.create_table(
        "produtos_fornecedores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=False),
        sa.Column("fornecedor_id", sa.Integer(), nullable=False),
        sa.Column("codigo_fornecedor", sa.String(80), nullable=True),
        sa.Column("custo_referencia", sa.Numeric(12, 2), nullable=True),
        sa.Column("preferencial", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"]),
        sa.ForeignKeyConstraint(["fornecedor_id"], ["fornecedores.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "produto_id", "fornecedor_id", name="uq_produto_fornecedor"
        ),
        sa.CheckConstraint(
            "custo_referencia IS NULL OR custo_referencia >= 0",
            name="ck_produto_fornecedor_custo_nao_negativo",
        ),
    )
    op.create_index(
        "ix_produtos_fornecedores_produto_id",
        "produtos_fornecedores",
        ["produto_id"],
    )
    op.create_index(
        "ix_produtos_fornecedores_fornecedor_id",
        "produtos_fornecedores",
        ["fornecedor_id"],
    )
    op.create_index(
        "uq_produto_fornecedor_preferencial",
        "produtos_fornecedores",
        ["produto_id"],
        unique=True,
        postgresql_where=sa.text("preferencial = true"),
    )
    op.execute(
        sa.text(
            "INSERT INTO produtos_fornecedores "
            "(produto_id, fornecedor_id, preferencial, ativo, created_at, updated_at) "
            "SELECT id, fornecedor_id, TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP "
            "FROM produtos"
        )
    )

    op.create_table(
        "historicos_custo_produto",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=False),
        sa.Column("fornecedor_id", sa.Integer(), nullable=True),
        sa.Column("custo", sa.Numeric(12, 2), nullable=False),
        sa.Column("registrado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("origem", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"]),
        sa.ForeignKeyConstraint(["fornecedor_id"], ["fornecedores.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("custo >= 0", name="ck_historico_custo_nao_negativo"),
    )
    op.create_index(
        "ix_historicos_custo_produto_produto_id",
        "historicos_custo_produto",
        ["produto_id"],
    )
    op.execute(
        sa.text(
            "INSERT INTO historicos_custo_produto "
            "(produto_id, fornecedor_id, custo, registrado_em, origem, created_at) "
            "SELECT id, fornecedor_id, preco_custo, CURRENT_TIMESTAMP, "
            "'migration_20260911_0004', CURRENT_TIMESTAMP FROM produtos"
        )
    )


def downgrade() -> None:
    op.drop_index(
        "ix_historicos_custo_produto_produto_id",
        table_name="historicos_custo_produto",
    )
    op.drop_table("historicos_custo_produto")
    op.drop_index(
        "uq_produto_fornecedor_preferencial", table_name="produtos_fornecedores"
    )
    op.drop_index(
        "ix_produtos_fornecedores_fornecedor_id", table_name="produtos_fornecedores"
    )
    op.drop_index(
        "ix_produtos_fornecedores_produto_id", table_name="produtos_fornecedores"
    )
    op.drop_table("produtos_fornecedores")
    op.drop_constraint("ck_produtos_estoque_minimo_nao_negativo", "produtos", type_="check")
    op.drop_constraint("fk_produtos_unidade_medida", "produtos", type_="foreignkey")
    op.drop_constraint("fk_produtos_categoria_id", "produtos", type_="foreignkey")
    op.drop_constraint("uq_produtos_codigo_barras", "produtos", type_="unique")
    op.drop_constraint("uq_produtos_sku", "produtos", type_="unique")
    for column in ("estoque_minimo", "ativo", "unidade_medida", "categoria_id", "codigo_barras", "sku"):
        op.drop_column("produtos", column)
    op.drop_table("categorias_produto")
    op.drop_table("unidades_medida")
