from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, inspect

from app.models import (
    CategoriaProduto,
    Cliente,
    ConfiguracaoEstoque,
    DepositoEstoque,
    DevolucaoVenda,
    Fornecedor,
    Funcionario,
    HistoricoCustoProduto,
    InventarioEstoque,
    LogAuditoria,
    MovimentacaoEstoque,
    Orcamento,
    PedidoCompra,
    PedidoVenda,
    Produto,
    ProdutoFornecedor,
    RecebimentoCompra,
    SessaoAutenticacao,
    TituloFinanceiro,
    Usuario,
    Venda,
    VendaItem,
)

EXPECTED_COLUMNS = {
    "clientes": {
        "id",
        "nome",
        "cidade",
        "estado",
        "rua",
        "numero",
        "complemento",
        "created_at",
        "updated_at",
    },
    "fornecedores": {
        "id",
        "nome",
        "cidade",
        "estado",
        "rua",
        "numero",
        "cnpj",
        "complemento",
        "created_at",
        "updated_at",
    },
    "funcionarios": {
        "id",
        "nome_completo",
        "cidade",
        "estado",
        "rua",
        "numero",
        "cpf",
        "data_nascimento",
        "complemento",
        "rg",
        "ativo",
        "created_at",
        "updated_at",
    },
    "produtos": {
        "id",
        "nome",
        "sku",
        "codigo_barras",
        "categoria",
        "categoria_id",
        "unidade_medida",
        "ativo",
        "estoque_minimo",
        "preco_custo",
        "preco_venda",
        "fornecedor_id",
        "created_at",
        "updated_at",
    },
    "vendas": {
        "id",
        "cliente_id",
        "funcionario_id",
        "data_venda",
        "status",
        "cancelada_em",
        "motivo_cancelamento",
        "observacao",
        "created_at",
        "updated_at",
    },
    "venda_itens": {
        "id",
        "venda_id",
        "produto_id",
        "quantidade",
        "preco_unitario",
        "fornecedor_id",
        "created_at",
        "updated_at",
    },
    "usuarios": {
        "id",
        "nome",
        "email",
        "senha_hash",
        "ativo",
        "role",
        "funcionario_id",
        "created_at",
        "updated_at",
    },
    "sessoes_autenticacao": {
        "id",
        "usuario_id",
        "token_hash",
        "expires_at",
        "revoked_at",
        "created_at",
    },
    "logs_auditoria": {
        "id",
        "usuario_id",
        "acao",
        "entidade",
        "entidade_id",
        "metadata_json",
        "created_at",
    },
    "unidades_medida": {"id", "codigo", "nome", "ativo"},
    "categorias_produto": {
        "id",
        "nome",
        "ativo",
        "created_at",
        "updated_at",
    },
    "produtos_fornecedores": {
        "id",
        "produto_id",
        "fornecedor_id",
        "codigo_fornecedor",
        "custo_referencia",
        "preferencial",
        "ativo",
        "created_at",
        "updated_at",
    },
    "historicos_custo_produto": {
        "id",
        "produto_id",
        "fornecedor_id",
        "custo",
        "registrado_em",
        "origem",
        "created_at",
    },
    "condicoes_pagamento": {"id", "codigo", "nome", "descricao", "ativo"},
    "orcamentos": {
        "id",
        "numero",
        "cliente_id",
        "funcionario_id",
        "condicao_pagamento_id",
        "validade",
        "desconto",
        "acrescimo",
        "frete",
        "status",
        "observacao",
        "created_at",
        "updated_at",
    },
    "orcamento_itens": {
        "id",
        "orcamento_id",
        "produto_id",
        "produto_nome",
        "sku",
        "fornecedor_id",
        "fornecedor_nome",
        "quantidade",
        "preco_unitario",
        "desconto",
        "acrescimo",
    },
    "pedidos_venda": {
        "id",
        "numero",
        "cliente_id",
        "funcionario_id",
        "orcamento_id",
        "venda_id",
        "condicao_pagamento_id",
        "desconto",
        "acrescimo",
        "frete",
        "status",
        "observacao",
        "created_at",
        "updated_at",
    },
    "pedido_venda_itens": {
        "id",
        "pedido_id",
        "produto_id",
        "produto_nome",
        "sku",
        "fornecedor_id",
        "fornecedor_nome",
        "quantidade",
        "preco_unitario",
        "desconto",
        "acrescimo",
    },
    "depositos_estoque": {
        "id",
        "codigo",
        "nome",
        "ativo",
        "padrao",
        "created_at",
        "updated_at",
    },
    "configuracoes_estoque": {"id", "permitir_saldo_negativo", "updated_at"},
    "movimentacoes_estoque": {
        "id",
        "produto_id",
        "deposito_id",
        "tipo",
        "quantidade",
        "data_movimentacao",
        "origem",
        "documento_tipo",
        "documento_id",
        "movimento_origem_id",
        "usuario_id",
        "observacao",
        "chave_idempotencia",
        "created_at",
    },
    "inventarios_estoque": {
        "id",
        "deposito_id",
        "data_inventario",
        "status",
        "usuario_id",
        "observacao",
        "created_at",
        "updated_at",
    },
    "inventarios_estoque_itens": {
        "id",
        "inventario_id",
        "produto_id",
        "saldo_sistema",
        "quantidade_contada",
        "diferenca",
    },
    "pedidos_compra": {
        "id",
        "numero",
        "fornecedor_id",
        "status",
        "previsao_entrega",
        "observacao",
        "created_at",
        "updated_at",
    },
    "pedido_compra_itens": {
        "id",
        "pedido_id",
        "produto_id",
        "produto_nome",
        "sku",
        "quantidade",
        "quantidade_recebida",
        "custo_unitario",
    },
    "recebimentos_compra": {
        "id",
        "pedido_id",
        "data_recebimento",
        "status",
        "usuario_id",
        "observacao",
        "created_at",
        "updated_at",
    },
    "recebimentos_compra_itens": {
        "id",
        "recebimento_id",
        "pedido_item_id",
        "produto_id",
        "quantidade",
        "custo_efetivo",
    },
    "devolucoes_venda": {
        "id",
        "venda_id",
        "status",
        "motivo",
        "usuario_id",
        "created_at",
        "updated_at",
    },
    "devolucoes_venda_itens": {
        "id",
        "devolucao_id",
        "venda_item_id",
        "produto_id",
        "produto_nome",
        "quantidade",
        "preco_unitario",
    },
    "categorias_financeiras": {"id", "nome", "tipo", "ativo"},
    "contas_financeiras": {"id", "nome", "saldo_inicial", "ativo"},
    "titulos_financeiros": {
        "id",
        "numero",
        "tipo",
        "cliente_id",
        "fornecedor_id",
        "categoria_id",
        "origem_tipo",
        "origem_id",
        "valor_original",
        "descricao",
        "created_at",
        "updated_at",
    },
    "parcelas_financeiras": {
        "id",
        "titulo_id",
        "numero",
        "vencimento",
        "valor",
    },
    "liquidacoes_financeiras": {
        "id",
        "parcela_id",
        "conta_id",
        "valor",
        "data_liquidacao",
        "status",
        "observacao",
        "created_at",
    },
    "modulos_erp": {"id", "codigo", "nome", "ativo", "ordem"},
    "configuracoes_aparencia": {
        "id",
        "nome_sistema",
        "logo_url",
        "cor_primaria",
        "cor_secundaria",
        "cor_destaque",
        "cor_fundo",
        "cor_superficie",
        "cor_texto",
        "cor_texto_primario",
        "cor_texto_secundario",
        "cor_texto_mudo",
        "cor_titulo",
        "cor_link",
        "cor_sobre_primaria",
        "cor_sobre_secundaria",
        "cor_sobre_destaque",
        "cor_tabela_cabecalho",
        "cor_tabela_corpo",
        "cor_tabela_fundo",
        "cor_tabela_borda",
        "cor_perigo",
        "cor_sucesso",
        "cor_aviso",
        "raio_controle",
        "raio_card",
        "rotulo_dashboard",
        "rotulo_clientes",
        "rotulo_produtos",
        "rotulo_funcionarios",
        "rotulo_fornecedores",
        "rotulo_vendas",
        "rotulo_nova_venda",
    },
    "configuracoes_aparencia_paginas": {
        "id",
        "pagina",
        "cor_fundo",
        "cor_superficie",
        "cor_titulo",
        "cor_texto_primario",
        "cor_texto_secundario",
        "cor_texto_mudo",
        "cor_destaque",
        "cor_link",
    },
    "configuracoes_aparencia_elementos": {
        "id",
        "customization_key",
        "customization_type",
        "customization_group",
        "pagina",
        "properties",
    },
    "cliente_campos": {"id", "nome", "tipo", "opcoes", "obrigatorio", "ativo", "ordem"},
    "cliente_campos_valores": {"id", "cliente_id", "campo_id", "valor"},
    "produto_campos": {"id", "nome", "tipo", "opcoes", "obrigatorio", "ativo", "ordem"},
    "produto_campos_valores": {"id", "produto_id", "campo_id", "valor"},
    "funcionario_campos": {
        "id",
        "nome",
        "tipo",
        "opcoes",
        "obrigatorio",
        "ativo",
        "ordem",
    },
    "funcionario_campos_valores": {"id", "funcionario_id", "campo_id", "valor"},
    "fornecedor_campos": {
        "id",
        "nome",
        "tipo",
        "opcoes",
        "obrigatorio",
        "ativo",
        "ordem",
    },
    "fornecedor_campos_valores": {"id", "fornecedor_id", "campo_id", "valor"},
}


def test_v1_tables_have_exactly_the_approved_columns() -> None:
    assert set(EXPECTED_COLUMNS) == set(Cliente.metadata.tables)

    for table_name, expected_columns in EXPECTED_COLUMNS.items():
        assert (
            set(Cliente.metadata.tables[table_name].columns.keys()) == expected_columns
        )


def test_only_approved_columns_are_nullable() -> None:
    nullable_columns = {
        table_name: {column.name for column in table.columns if column.nullable}
        for table_name, table in Cliente.metadata.tables.items()
    }

    assert nullable_columns == {
        "clientes": {"complemento"},
        "fornecedores": {"complemento"},
        "funcionarios": {"complemento", "rg"},
        "produtos": {"categoria_id", "codigo_barras"},
        "vendas": {"cancelada_em", "motivo_cancelamento", "observacao"},
        "venda_itens": set(),
        "usuarios": {"funcionario_id"},
        "sessoes_autenticacao": {"revoked_at"},
        "logs_auditoria": {"usuario_id", "entidade_id", "metadata_json"},
        "unidades_medida": set(),
        "categorias_produto": set(),
        "produtos_fornecedores": {"codigo_fornecedor", "custo_referencia"},
        "historicos_custo_produto": {"fornecedor_id"},
        "condicoes_pagamento": {"descricao"},
        "orcamentos": {
            "funcionario_id",
            "condicao_pagamento_id",
            "validade",
            "observacao",
        },
        "orcamento_itens": set(),
        "pedidos_venda": {
            "funcionario_id",
            "orcamento_id",
            "venda_id",
            "condicao_pagamento_id",
            "observacao",
        },
        "pedido_venda_itens": set(),
        "depositos_estoque": set(),
        "configuracoes_estoque": set(),
        "movimentacoes_estoque": {
            "documento_tipo",
            "documento_id",
            "movimento_origem_id",
            "usuario_id",
            "observacao",
            "chave_idempotencia",
        },
        "inventarios_estoque": {"usuario_id", "observacao"},
        "inventarios_estoque_itens": set(),
        "pedidos_compra": {"previsao_entrega", "observacao"},
        "pedido_compra_itens": set(),
        "recebimentos_compra": {"usuario_id", "observacao"},
        "recebimentos_compra_itens": set(),
        "devolucoes_venda": {"usuario_id"},
        "devolucoes_venda_itens": set(),
        "categorias_financeiras": set(),
        "contas_financeiras": set(),
        "titulos_financeiros": {
            "cliente_id",
            "fornecedor_id",
            "categoria_id",
            "origem_tipo",
            "origem_id",
            "descricao",
        },
        "parcelas_financeiras": set(),
        "liquidacoes_financeiras": {"observacao"},
        "modulos_erp": set(),
        "configuracoes_aparencia": {"logo_url"},
        "configuracoes_aparencia_paginas": {
            "cor_fundo",
            "cor_superficie",
            "cor_titulo",
            "cor_texto_primario",
            "cor_texto_secundario",
            "cor_texto_mudo",
            "cor_destaque",
            "cor_link",
        },
        "configuracoes_aparencia_elementos": {
            "customization_group",
            "pagina",
        },
        "cliente_campos": {"opcoes"},
        "cliente_campos_valores": {"valor"},
        "produto_campos": {"opcoes"},
        "produto_campos_valores": {"valor"},
        "funcionario_campos": {"opcoes"},
        "funcionario_campos_valores": {"valor"},
        "fornecedor_campos": {"opcoes"},
        "fornecedor_campos_valores": {"valor"},
    }


def test_money_and_date_types_are_explicit() -> None:
    produtos = Cliente.metadata.tables["produtos"]
    itens = Cliente.metadata.tables["venda_itens"]
    funcionarios = Cliente.metadata.tables["funcionarios"]
    vendas = Cliente.metadata.tables["vendas"]

    for column_name in ("preco_custo", "preco_venda"):
        column_type = produtos.c[column_name].type
        assert isinstance(column_type, Numeric)
        assert (column_type.precision, column_type.scale) == (12, 2)

    item_price_type = itens.c.preco_unitario.type
    quantity_type = itens.c.quantidade.type
    supplier_id_type = itens.c.fornecedor_id.type
    assert isinstance(item_price_type, Numeric)
    assert (item_price_type.precision, item_price_type.scale) == (12, 2)
    assert isinstance(quantity_type, Numeric)
    assert (quantity_type.precision, quantity_type.scale) == (12, 3)
    assert isinstance(supplier_id_type, Integer)
    assert itens.c.fornecedor_id.nullable is False
    assert isinstance(funcionarios.c.data_nascimento.type, Date)
    assert isinstance(funcionarios.c.ativo.type, Boolean)
    assert funcionarios.c.ativo.nullable is False
    assert funcionarios.c.ativo.default.arg is True
    assert funcionarios.c.ativo.server_default is not None
    assert isinstance(vendas.c.data_venda.type, DateTime)
    assert vendas.c.data_venda.type.timezone is True
    assert isinstance(vendas.c.created_at.type, DateTime)
    assert vendas.c.created_at.type.timezone is True
    assert isinstance(vendas.c.updated_at.type, DateTime)
    assert vendas.c.updated_at.type.timezone is True


def test_operational_timestamps_and_sale_defaults_are_declared() -> None:
    for model in (
        Cliente,
        Fornecedor,
        Funcionario,
        Produto,
        Venda,
        VendaItem,
        Usuario,
        CategoriaProduto,
        ProdutoFornecedor,
        Orcamento,
        PedidoVenda,
        DepositoEstoque,
        InventarioEstoque,
        PedidoCompra,
        RecebimentoCompra,
        DevolucaoVenda,
        TituloFinanceiro,
    ):
        created_at = model.__table__.c.created_at
        updated_at = model.__table__.c.updated_at
        assert callable(created_at.default.arg)
        assert callable(updated_at.default.arg)
        assert callable(updated_at.onupdate.arg)

    for model in (SessaoAutenticacao, LogAuditoria):
        assert callable(model.__table__.c.created_at.default.arg)
    assert callable(HistoricoCustoProduto.__table__.c.created_at.default.arg)
    assert callable(MovimentacaoEstoque.__table__.c.created_at.default.arg)
    assert callable(ConfiguracaoEstoque.__table__.c.updated_at.default.arg)

    assert Venda.__table__.c.status.default.arg == "CONCLUIDA"
    assert Venda.__table__.c.status.server_default is not None


def test_constraints_and_foreign_keys_are_named_and_restrictive() -> None:
    expected_constraints = {
        "produtos": {
            "ck_produtos_preco_custo_nao_negativo",
            "ck_produtos_preco_venda_nao_negativo",
        },
        "venda_itens": {
            "ck_venda_itens_quantidade_positiva",
            "ck_venda_itens_preco_unitario_nao_negativo",
        },
        "vendas": {"ck_vendas_status_valido"},
    }

    for table_name, constraint_names in expected_constraints.items():
        table = Cliente.metadata.tables[table_name]
        actual_names = {
            constraint.name
            for constraint in table.constraints
            if constraint.name is not None
        }
        assert constraint_names <= actual_names

    assert {
        constraint.name
        for constraint in Cliente.metadata.tables["fornecedores"].constraints
    } >= {"uq_fornecedores_cnpj"}
    assert {
        constraint.name
        for constraint in Cliente.metadata.tables["funcionarios"].constraints
    } >= {"uq_funcionarios_cpf"}
    supplier_foreign_keys = Cliente.metadata.tables[
        "venda_itens"
    ].foreign_key_constraints
    assert any(
        foreign_key.column_keys == ["fornecedor_id"]
        and str(foreign_key.elements[0].target_fullname) == "fornecedores.id"
        for foreign_key in supplier_foreign_keys
    )

    for table in Cliente.metadata.tables.values():
        for foreign_key in table.foreign_key_constraints:
            assert foreign_key.ondelete is None


def test_relationships_do_not_configure_delete_cascades() -> None:
    for model in (Cliente, Fornecedor, Funcionario, Produto, Venda, VendaItem):
        mapper = inspect(model)
        for relationship in mapper.relationships:
            assert "delete" not in relationship.cascade
            assert "delete-orphan" not in relationship.cascade
