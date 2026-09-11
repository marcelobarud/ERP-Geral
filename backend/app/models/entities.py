"""Entidades persistentes da V1.

Valores monetários usam ``NUMERIC(12, 2)``, com duas casas decimais e limite
comercial de até 10 dígitos inteiros. Quantidades usam ``NUMERIC(12, 3)`` para
permitir itens fracionáveis sem usar ponto flutuante binário.
"""

from datetime import date, datetime, timezone
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


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    cidade: Mapped[str] = mapped_column(String(100), nullable=False)
    estado: Mapped[str] = mapped_column(String(2), nullable=False)
    rua: Mapped[str] = mapped_column(String(255), nullable=False)
    numero: Mapped[str] = mapped_column(String(20), nullable=False)
    complemento: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    vendas: Mapped[list["Venda"]] = relationship(
        back_populates="cliente",
        passive_deletes=True,
    )


class Fornecedor(Base):
    __tablename__ = "fornecedores"
    __table_args__ = (
        UniqueConstraint("cnpj", name="uq_fornecedores_cnpj"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    cidade: Mapped[str] = mapped_column(String(100), nullable=False)
    estado: Mapped[str] = mapped_column(String(2), nullable=False)
    rua: Mapped[str] = mapped_column(String(255), nullable=False)
    numero: Mapped[str] = mapped_column(String(20), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(18), nullable=False)
    complemento: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    produtos: Mapped[list["Produto"]] = relationship(
        back_populates="fornecedor",
        passive_deletes=True,
    )


class Funcionario(Base):
    __tablename__ = "funcionarios"
    __table_args__ = (
        UniqueConstraint("cpf", name="uq_funcionarios_cpf"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome_completo: Mapped[str] = mapped_column(String(255), nullable=False)
    cidade: Mapped[str] = mapped_column(String(100), nullable=False)
    estado: Mapped[str] = mapped_column(String(2), nullable=False)
    rua: Mapped[str] = mapped_column(String(255), nullable=False)
    numero: Mapped[str] = mapped_column(String(20), nullable=False)
    cpf: Mapped[str] = mapped_column(String(14), nullable=False)
    data_nascimento: Mapped[date] = mapped_column(Date, nullable=False)
    complemento: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rg: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ativo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    vendas: Mapped[list["Venda"]] = relationship(
        back_populates="funcionario",
        passive_deletes=True,
    )


class Produto(Base):
    __tablename__ = "produtos"
    __table_args__ = (
        CheckConstraint(
            "preco_custo >= 0",
            name="ck_produtos_preco_custo_nao_negativo",
        ),
        CheckConstraint(
            "preco_venda >= 0",
            name="ck_produtos_preco_venda_nao_negativo",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    categoria: Mapped[str] = mapped_column(String(100), nullable=False)
    preco_custo: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    preco_venda: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    fornecedor_id: Mapped[int] = mapped_column(
        ForeignKey("fornecedores.id"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    fornecedor: Mapped[Fornecedor] = relationship(back_populates="produtos")
    itens: Mapped[list["VendaItem"]] = relationship(
        back_populates="produto",
        passive_deletes=True,
    )


class Venda(Base):
    __tablename__ = "vendas"
    __table_args__ = (
        CheckConstraint(
            "status IN ('CONCLUIDA', 'CANCELADA')",
            name="ck_vendas_status_valido",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id"),
        nullable=False,
        index=True,
    )
    funcionario_id: Mapped[int] = mapped_column(
        ForeignKey("funcionarios.id"),
        nullable=False,
        index=True,
    )
    data_venda: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="CONCLUIDA", server_default="CONCLUIDA"
    )
    cancelada_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    motivo_cancelamento: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    observacao: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    cliente: Mapped[Cliente] = relationship(back_populates="vendas")
    funcionario: Mapped[Funcionario] = relationship(back_populates="vendas")
    itens: Mapped[list["VendaItem"]] = relationship(
        back_populates="venda",
        passive_deletes=True,
    )


class VendaItem(Base):
    __tablename__ = "venda_itens"
    __table_args__ = (
        CheckConstraint(
            "quantidade > 0",
            name="ck_venda_itens_quantidade_positiva",
        ),
        CheckConstraint(
            "preco_unitario >= 0",
            name="ck_venda_itens_preco_unitario_nao_negativo",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    venda_id: Mapped[int] = mapped_column(
        ForeignKey("vendas.id"),
        nullable=False,
        index=True,
    )
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"),
        nullable=False,
        index=True,
    )
    quantidade: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
    )
    preco_unitario: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    fornecedor_id: Mapped[int] = mapped_column(
        ForeignKey("fornecedores.id"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    venda: Mapped[Venda] = relationship(back_populates="itens")
    produto: Mapped[Produto] = relationship(back_populates="itens")
    fornecedor: Mapped[Fornecedor] = relationship(
        foreign_keys=[fornecedor_id],
        viewonly=True,
    )
