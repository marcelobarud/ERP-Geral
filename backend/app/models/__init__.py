"""Models SQLAlchemy do domínio mínimo da V1."""

from app.models.appearance import (
    AppearanceSettings,
    ElementAppearanceOverride,
    PageAppearanceSettings,
)
from app.models.auth import LogAuditoria, SessaoAutenticacao, Usuario
from app.models.catalog import (
    CategoriaProduto,
    HistoricoCustoProduto,
    ProdutoFornecedor,
    UnidadeMedida,
)
from app.models.commercial import (
    CondicaoPagamento,
    Orcamento,
    OrcamentoItem,
    PedidoVenda,
    PedidoVendaItem,
)
from app.models.custom_fields import (
    ClienteCampo,
    ClienteCampoValor,
    FornecedorCampo,
    FornecedorCampoValor,
    FuncionarioCampo,
    FuncionarioCampoValor,
    ProdutoCampo,
    ProdutoCampoValor,
)
from app.models.entities import (
    Cliente,
    Fornecedor,
    Funcionario,
    Produto,
    Venda,
    VendaItem,
)
from app.models.inventory import (
    ConfiguracaoEstoque,
    DepositoEstoque,
    InventarioEstoque,
    InventarioEstoqueItem,
    MovimentacaoEstoque,
)
from app.models.purchases import (
    PedidoCompra,
    PedidoCompraItem,
    RecebimentoCompra,
    RecebimentoCompraItem,
)
from app.models.returns import DevolucaoVenda, DevolucaoVendaItem

__all__ = [
    "Cliente",
    "Fornecedor",
    "Funcionario",
    "Produto",
    "Venda",
    "VendaItem",
    "Usuario",
    "SessaoAutenticacao",
    "LogAuditoria",
    "UnidadeMedida",
    "CategoriaProduto",
    "ProdutoFornecedor",
    "HistoricoCustoProduto",
    "CondicaoPagamento",
    "Orcamento",
    "OrcamentoItem",
    "PedidoVenda",
    "PedidoVendaItem",
    "DepositoEstoque",
    "ConfiguracaoEstoque",
    "MovimentacaoEstoque",
    "InventarioEstoque",
    "InventarioEstoqueItem",
    "PedidoCompra",
    "PedidoCompraItem",
    "RecebimentoCompra",
    "RecebimentoCompraItem",
    "DevolucaoVenda",
    "DevolucaoVendaItem",
    "AppearanceSettings",
    "PageAppearanceSettings",
    "ElementAppearanceOverride",
    "ClienteCampo",
    "ClienteCampoValor",
    "ProdutoCampo",
    "ProdutoCampoValor",
    "FuncionarioCampo",
    "FuncionarioCampoValor",
    "FornecedorCampo",
    "FornecedorCampoValor",
]
