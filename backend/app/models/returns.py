"""Devoluções de vendas e seus snapshots."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.auth import Usuario
from app.models.entities import Produto, Venda, VendaItem, utc_now


class DevolucaoVenda(Base):
    __tablename__ = "devolucoes_venda"
    __table_args__ = (
        CheckConstraint(
            "status IN ('RASCUNHO', 'APROVADA', 'CANCELADA')",
            name="ck_devolucoes_venda_status_valido",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    venda_id: Mapped[int] = mapped_column(
        ForeignKey("vendas.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="RASCUNHO", server_default="RASCUNHO"
    )
    motivo: Mapped[str] = mapped_column(String(500), nullable=False)
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    venda: Mapped[Venda] = relationship()
    usuario: Mapped[Usuario | None] = relationship()
    itens: Mapped[list["DevolucaoVendaItem"]] = relationship(
        back_populates="devolucao", cascade="all, delete-orphan"
    )


class DevolucaoVendaItem(Base):
    __tablename__ = "devolucoes_venda_itens"
    __table_args__ = (
        CheckConstraint("quantidade > 0", name="ck_devolucao_quantidade_positiva"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    devolucao_id: Mapped[int] = mapped_column(
        ForeignKey("devolucoes_venda.id"), nullable=False, index=True
    )
    venda_item_id: Mapped[int] = mapped_column(
        ForeignKey("venda_itens.id"), nullable=False, index=True
    )
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"), nullable=False
    )
    produto_nome: Mapped[str] = mapped_column(String(255), nullable=False)
    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    devolucao: Mapped[DevolucaoVenda] = relationship(back_populates="itens")
    venda_item: Mapped[VendaItem] = relationship()
    produto: Mapped[Produto] = relationship()
