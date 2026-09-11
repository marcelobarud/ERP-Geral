"""Módulos ativos e configurações de produto do ERP."""

from sqlalchemy import Boolean, Integer, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ModuloERP(Base):
    __tablename__ = "modulos_erp"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    ativo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    ordem: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
