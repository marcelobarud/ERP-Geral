"""Documentos comerciais de pré-venda do ERP."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.entities import (
    Cliente,
    Fornecedor,
    Funcionario,
    Produto,
    Venda,
    utc_now,
)


class CondicaoPagamento(Base):
    __tablename__ = "condicoes_pagamento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ativo: Mapped[bool] = mapped_column(
        nullable=False, default=True, server_default="true"
    )


class Orcamento(Base):
    __tablename__ = "orcamentos"
    __table_args__ = (
        CheckConstraint(
            "status IN ('RASCUNHO', 'ENVIADO', 'APROVADO', 'RECUSADO', "
            "'EXPIRADO', 'CANCELADO')",
            name="ck_orcamentos_status_valido",
        ),
        CheckConstraint("desconto >= 0", name="ck_orcamentos_desconto_nao_negativo"),
        CheckConstraint("acrescimo >= 0", name="ck_orcamentos_acrescimo_nao_negativo"),
        CheckConstraint("frete >= 0", name="ck_orcamentos_frete_nao_negativo"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id"), nullable=False, index=True
    )
    funcionario_id: Mapped[int | None] = mapped_column(
        ForeignKey("funcionarios.id"), nullable=True, index=True
    )
    condicao_pagamento_id: Mapped[int | None] = mapped_column(
        ForeignKey("condicoes_pagamento.id"), nullable=True
    )
    validade: Mapped[date | None] = mapped_column(Date, nullable=True)
    desconto: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default="0"
    )
    acrescimo: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default="0"
    )
    frete: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default="0"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="RASCUNHO", server_default="RASCUNHO"
    )
    observacao: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    cliente: Mapped[Cliente] = relationship()
    funcionario: Mapped[Funcionario | None] = relationship()
    condicao_pagamento: Mapped[CondicaoPagamento | None] = relationship()
    pedido: Mapped["PedidoVenda | None"] = relationship(
        back_populates="orcamento", uselist=False
    )
    itens: Mapped[list["OrcamentoItem"]] = relationship(
        back_populates="orcamento", cascade="all, delete-orphan"
    )


class OrcamentoItem(Base):
    __tablename__ = "orcamento_itens"
    __table_args__ = (
        CheckConstraint(
            "quantidade > 0", name="ck_orcamento_itens_quantidade_positiva"
        ),
        CheckConstraint(
            "preco_unitario >= 0", name="ck_orcamento_itens_preco_nao_negativo"
        ),
        CheckConstraint(
            "desconto >= 0", name="ck_orcamento_itens_desconto_nao_negativo"
        ),
        CheckConstraint(
            "acrescimo >= 0", name="ck_orcamento_itens_acrescimo_nao_negativo"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    orcamento_id: Mapped[int] = mapped_column(
        ForeignKey("orcamentos.id"), nullable=False, index=True
    )
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"), nullable=False, index=True
    )
    produto_nome: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(80), nullable=False)
    fornecedor_id: Mapped[int] = mapped_column(
        ForeignKey("fornecedores.id"), nullable=False
    )
    fornecedor_nome: Mapped[str] = mapped_column(String(255), nullable=False)
    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    desconto: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default="0"
    )
    acrescimo: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default="0"
    )

    orcamento: Mapped[Orcamento] = relationship(back_populates="itens")
    produto: Mapped[Produto] = relationship()
    fornecedor: Mapped[Fornecedor] = relationship()


class PedidoVenda(Base):
    __tablename__ = "pedidos_venda"
    __table_args__ = (
        CheckConstraint(
            "status IN ('RASCUNHO', 'CONFIRMADO', 'CONCLUIDO', 'CANCELADO')",
            name="ck_pedidos_venda_status_valido",
        ),
        CheckConstraint("desconto >= 0", name="ck_pedidos_venda_desconto_nao_negativo"),
        CheckConstraint(
            "acrescimo >= 0", name="ck_pedidos_venda_acrescimo_nao_negativo"
        ),
        CheckConstraint("frete >= 0", name="ck_pedidos_venda_frete_nao_negativo"),
        UniqueConstraint("orcamento_id", name="uq_pedido_venda_orcamento"),
        UniqueConstraint("venda_id", name="uq_pedido_venda_venda"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id"), nullable=False, index=True
    )
    funcionario_id: Mapped[int | None] = mapped_column(
        ForeignKey("funcionarios.id"), nullable=True, index=True
    )
    orcamento_id: Mapped[int | None] = mapped_column(
        ForeignKey("orcamentos.id"), nullable=True, index=True
    )
    venda_id: Mapped[int | None] = mapped_column(
        ForeignKey("vendas.id"), nullable=True, index=True
    )
    condicao_pagamento_id: Mapped[int | None] = mapped_column(
        ForeignKey("condicoes_pagamento.id"), nullable=True
    )
    desconto: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default="0"
    )
    acrescimo: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default="0"
    )
    frete: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default="0"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="RASCUNHO", server_default="RASCUNHO"
    )
    observacao: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    cliente: Mapped[Cliente] = relationship()
    funcionario: Mapped[Funcionario | None] = relationship()
    orcamento: Mapped[Orcamento | None] = relationship(back_populates="pedido")
    venda: Mapped[Venda | None] = relationship()
    condicao_pagamento: Mapped[CondicaoPagamento | None] = relationship()
    itens: Mapped[list["PedidoVendaItem"]] = relationship(
        back_populates="pedido", cascade="all, delete-orphan"
    )


class PedidoVendaItem(Base):
    __tablename__ = "pedido_venda_itens"
    __table_args__ = (
        CheckConstraint("quantidade > 0", name="ck_pedido_itens_quantidade_positiva"),
        CheckConstraint(
            "preco_unitario >= 0", name="ck_pedido_itens_preco_nao_negativo"
        ),
        CheckConstraint(
            "desconto >= 0", name="ck_pedido_itens_desconto_nao_negativo"
        ),
        CheckConstraint(
            "acrescimo >= 0", name="ck_pedido_itens_acrescimo_nao_negativo"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pedido_id: Mapped[int] = mapped_column(
        ForeignKey("pedidos_venda.id"), nullable=False, index=True
    )
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"), nullable=False, index=True
    )
    produto_nome: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(80), nullable=False)
    fornecedor_id: Mapped[int] = mapped_column(
        ForeignKey("fornecedores.id"), nullable=False
    )
    fornecedor_nome: Mapped[str] = mapped_column(String(255), nullable=False)
    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    desconto: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default="0"
    )
    acrescimo: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default="0"
    )

    pedido: Mapped[PedidoVenda] = relationship(back_populates="itens")
    produto: Mapped[Produto] = relationship()
    fornecedor: Mapped[Fornecedor] = relationship()
