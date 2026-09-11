"""Catálogos e relações comerciais preparatórias do ERP."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    false,
    text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.entities import Fornecedor, Produto, utc_now


class UnidadeMedida(Base):
    __tablename__ = "unidades_medida"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    nome: Mapped[str] = mapped_column(String(80), nullable=False)
    ativo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )


class CategoriaProduto(Base):
    __tablename__ = "categorias_produto"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    ativo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    produtos: Mapped[list[Produto]] = relationship(
        back_populates="categoria_estruturada", passive_deletes=True
    )


class ProdutoFornecedor(Base):
    __tablename__ = "produtos_fornecedores"
    __table_args__ = (
        UniqueConstraint(
            "produto_id", "fornecedor_id", name="uq_produto_fornecedor"
        ),
        CheckConstraint(
            "custo_referencia IS NULL OR custo_referencia >= 0",
            name="ck_produto_fornecedor_custo_nao_negativo",
        ),
        Index(
            "uq_produto_fornecedor_preferencial",
            "produto_id",
            unique=True,
            postgresql_where=text("preferencial = true"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"), nullable=False, index=True
    )
    fornecedor_id: Mapped[int] = mapped_column(
        ForeignKey("fornecedores.id"), nullable=False, index=True
    )
    codigo_fornecedor: Mapped[str | None] = mapped_column(
        String(80), nullable=True
    )
    custo_referencia: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    preferencial: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    ativo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    produto: Mapped[Produto] = relationship(back_populates="fornecedores_adicionais")
    fornecedor: Mapped[Fornecedor] = relationship()


class HistoricoCustoProduto(Base):
    __tablename__ = "historicos_custo_produto"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"), nullable=False, index=True
    )
    fornecedor_id: Mapped[int | None] = mapped_column(
        ForeignKey("fornecedores.id"), nullable=True
    )
    custo: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    registrado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    origem: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    produto: Mapped[Produto] = relationship(back_populates="historico_custos")
    fornecedor: Mapped[Fornecedor | None] = relationship()
