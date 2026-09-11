"""Financeiro operacional: títulos, parcelas, liquidações e caixa."""

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
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.entities import Cliente, Fornecedor, utc_now


class CategoriaFinanceira(Base):
    __tablename__ = "categorias_financeiras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)
    ativo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )


class ContaFinanceira(Base):
    __tablename__ = "contas_financeiras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    saldo_inicial: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0"), server_default="0"
    )
    ativo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )


class TituloFinanceiro(Base):
    __tablename__ = "titulos_financeiros"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('RECEBER', 'PAGAR')", name="ck_titulos_financeiros_tipo_valido"
        ),
        CheckConstraint(
            "valor_original >= 0", name="ck_titulos_financeiros_valor_nao_negativo"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)
    cliente_id: Mapped[int | None] = mapped_column(
        ForeignKey("clientes.id"), nullable=True
    )
    fornecedor_id: Mapped[int | None] = mapped_column(
        ForeignKey("fornecedores.id"), nullable=True
    )
    categoria_id: Mapped[int | None] = mapped_column(
        ForeignKey("categorias_financeiras.id"), nullable=True
    )
    origem_tipo: Mapped[str | None] = mapped_column(String(40), nullable=True)
    origem_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    valor_original: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    cliente: Mapped[Cliente | None] = relationship()
    fornecedor: Mapped[Fornecedor | None] = relationship()
    parcelas: Mapped[list["ParcelaFinanceira"]] = relationship(
        back_populates="titulo", cascade="all, delete-orphan"
    )


class ParcelaFinanceira(Base):
    __tablename__ = "parcelas_financeiras"
    __table_args__ = (
        CheckConstraint(
            "valor >= 0", name="ck_parcelas_financeiras_valor_nao_negativo"
        ),
        CheckConstraint("numero > 0", name="ck_parcelas_financeiras_numero_positivo"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    titulo_id: Mapped[int] = mapped_column(
        ForeignKey("titulos_financeiros.id"), nullable=False, index=True
    )
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    vencimento: Mapped[date] = mapped_column(Date, nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    titulo: Mapped[TituloFinanceiro] = relationship(back_populates="parcelas")
    liquidacoes: Mapped[list["LiquidacaoFinanceira"]] = relationship(
        back_populates="parcela"
    )


class LiquidacaoFinanceira(Base):
    __tablename__ = "liquidacoes_financeiras"
    __table_args__ = (
        CheckConstraint("valor > 0", name="ck_liquidacoes_financeiras_valor_positivo"),
        CheckConstraint(
            "status IN ('CONFIRMADA', 'ESTORNADA')",
            name="ck_liquidacoes_financeiras_status_valido",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parcela_id: Mapped[int] = mapped_column(
        ForeignKey("parcelas_financeiras.id"), nullable=False, index=True
    )
    conta_id: Mapped[int] = mapped_column(
        ForeignKey("contas_financeiras.id"), nullable=False
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    data_liquidacao: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(12), nullable=False, default="CONFIRMADA", server_default="CONFIRMADA"
    )
    observacao: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    parcela: Mapped[ParcelaFinanceira] = relationship(back_populates="liquidacoes")
    conta: Mapped[ContaFinanceira] = relationship()
