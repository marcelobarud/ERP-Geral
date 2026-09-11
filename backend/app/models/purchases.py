"""Pedidos de compra e recebimentos."""

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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.auth import Usuario
from app.models.entities import Fornecedor, Produto, utc_now


class PedidoCompra(Base):
    __tablename__ = "pedidos_compra"
    __table_args__ = (
        CheckConstraint(
            "status IN ('RASCUNHO', 'EMITIDO', 'PARCIALMENTE_RECEBIDO', "
            "'RECEBIDO', 'CANCELADO')",
            name="ck_pedidos_compra_status_valido",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    fornecedor_id: Mapped[int] = mapped_column(
        ForeignKey("fornecedores.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, default="RASCUNHO", server_default="RASCUNHO"
    )
    previsao_entrega: Mapped[date | None] = mapped_column(Date, nullable=True)
    observacao: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    fornecedor: Mapped[Fornecedor] = relationship()
    itens: Mapped[list["PedidoCompraItem"]] = relationship(
        back_populates="pedido", cascade="all, delete-orphan"
    )
    recebimentos: Mapped[list["RecebimentoCompra"]] = relationship(
        back_populates="pedido"
    )


class PedidoCompraItem(Base):
    __tablename__ = "pedido_compra_itens"
    __table_args__ = (
        CheckConstraint("quantidade > 0", name="ck_pedido_compra_quantidade_positiva"),
        CheckConstraint(
            "custo_unitario >= 0", name="ck_pedido_compra_custo_nao_negativo"
        ),
        CheckConstraint(
            "quantidade_recebida >= 0",
            name="ck_pedido_compra_recebida_nao_negativa",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pedido_id: Mapped[int] = mapped_column(
        ForeignKey("pedidos_compra.id"), nullable=False, index=True
    )
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"), nullable=False, index=True
    )
    produto_nome: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(80), nullable=False)
    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    quantidade_recebida: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False, default=Decimal("0"), server_default="0"
    )
    custo_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    pedido: Mapped[PedidoCompra] = relationship(back_populates="itens")
    produto: Mapped[Produto] = relationship()


class RecebimentoCompra(Base):
    __tablename__ = "recebimentos_compra"
    __table_args__ = (
        CheckConstraint(
            "status IN ('RASCUNHO', 'CONFIRMADO', 'CANCELADO')",
            name="ck_recebimentos_compra_status_valido",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pedido_id: Mapped[int] = mapped_column(
        ForeignKey("pedidos_compra.id"), nullable=False, index=True
    )
    data_recebimento: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="RASCUNHO", server_default="RASCUNHO"
    )
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )
    observacao: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    pedido: Mapped[PedidoCompra] = relationship(back_populates="recebimentos")
    usuario: Mapped[Usuario | None] = relationship()
    itens: Mapped[list["RecebimentoCompraItem"]] = relationship(
        back_populates="recebimento", cascade="all, delete-orphan"
    )


class RecebimentoCompraItem(Base):
    __tablename__ = "recebimentos_compra_itens"
    __table_args__ = (
        CheckConstraint("quantidade > 0", name="ck_recebimento_quantidade_positiva"),
        CheckConstraint("custo_efetivo >= 0", name="ck_recebimento_custo_nao_negativo"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recebimento_id: Mapped[int] = mapped_column(
        ForeignKey("recebimentos_compra.id"), nullable=False, index=True
    )
    pedido_item_id: Mapped[int] = mapped_column(
        ForeignKey("pedido_compra_itens.id"), nullable=False, index=True
    )
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"), nullable=False
    )
    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    custo_efetivo: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    recebimento: Mapped[RecebimentoCompra] = relationship(back_populates="itens")
    pedido_item: Mapped[PedidoCompraItem] = relationship()
    produto: Mapped[Produto] = relationship()
