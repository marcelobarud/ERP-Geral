"""Estoque baseado em movimentações append-oriented."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.auth import Usuario
from app.models.entities import Produto, utc_now


class DepositoEstoque(Base):
    __tablename__ = "depositos_estoque"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    ativo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )


class ConfiguracaoEstoque(Base):
    __tablename__ = "configuracoes_estoque"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    permitir_saldo_negativo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )


class MovimentacaoEstoque(Base):
    __tablename__ = "movimentacoes_estoque"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('ENTRADA', 'SAIDA', 'AJUSTE_ENTRADA', 'AJUSTE_SAIDA', "
            "'DEVOLUCAO_ENTRADA', 'DEVOLUCAO_SAIDA', 'REVERSAO')",
            name="ck_movimentacoes_estoque_tipo_valido",
        ),
        CheckConstraint(
            "quantidade > 0",
            name="ck_movimentacoes_estoque_quantidade_positiva",
        ),
        UniqueConstraint(
            "chave_idempotencia", name="uq_movimentacoes_estoque_idempotencia"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"), nullable=False, index=True
    )
    deposito_id: Mapped[int] = mapped_column(
        ForeignKey("depositos_estoque.id"), nullable=False, index=True
    )
    tipo: Mapped[str] = mapped_column(String(24), nullable=False)
    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    data_movimentacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    origem: Mapped[str] = mapped_column(String(40), nullable=False)
    documento_tipo: Mapped[str | None] = mapped_column(String(40), nullable=True)
    documento_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    movimento_origem_id: Mapped[int | None] = mapped_column(
        ForeignKey("movimentacoes_estoque.id"), nullable=True
    )
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )
    observacao: Mapped[str | None] = mapped_column(String(500), nullable=True)
    chave_idempotencia: Mapped[str | None] = mapped_column(
        String(120), nullable=True, unique=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    produto: Mapped[Produto] = relationship()
    deposito: Mapped[DepositoEstoque] = relationship()
    usuario: Mapped[Usuario | None] = relationship()
    movimento_origem: Mapped["MovimentacaoEstoque | None"] = relationship(
        remote_side="MovimentacaoEstoque.id"
    )


class InventarioEstoque(Base):
    __tablename__ = "inventarios_estoque"
    __table_args__ = (
        CheckConstraint(
            "status IN ('RASCUNHO', 'CONFIRMADO', 'CANCELADO')",
            name="ck_inventarios_estoque_status_valido",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    deposito_id: Mapped[int] = mapped_column(
        ForeignKey("depositos_estoque.id"), nullable=False, index=True
    )
    data_inventario: Mapped[date] = mapped_column(Date, nullable=False)
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

    deposito: Mapped[DepositoEstoque] = relationship()
    usuario: Mapped[Usuario | None] = relationship()
    itens: Mapped[list["InventarioEstoqueItem"]] = relationship(
        back_populates="inventario", cascade="all, delete-orphan"
    )


class InventarioEstoqueItem(Base):
    __tablename__ = "inventarios_estoque_itens"
    __table_args__ = (
        CheckConstraint(
            "quantidade_contada >= 0",
            name="ck_inventarios_estoque_quantidade_contada_nao_negativa",
        ),
        UniqueConstraint(
            "inventario_id", "produto_id", name="uq_inventario_estoque_produto"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inventario_id: Mapped[int] = mapped_column(
        ForeignKey("inventarios_estoque.id"), nullable=False, index=True
    )
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"), nullable=False, index=True
    )
    saldo_sistema: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    quantidade_contada: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    diferenca: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)

    inventario: Mapped[InventarioEstoque] = relationship(back_populates="itens")
    produto: Mapped[Produto] = relationship()
