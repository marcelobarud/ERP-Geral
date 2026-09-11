"""Entidades de autenticação, sessões e auditoria do ERP."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.entities import utc_now


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("email", name="uq_usuarios_email"),
        CheckConstraint(
            "role IN ('ADMIN', 'MANAGER', 'OPERATOR')",
            name="ck_usuarios_role_valido",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    ativo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="OPERATOR", server_default="OPERATOR"
    )
    funcionario_id: Mapped[int | None] = mapped_column(
        ForeignKey("funcionarios.id"), nullable=True, unique=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    sessions: Mapped[list["SessaoAutenticacao"]] = relationship(
        back_populates="usuario", passive_deletes=True
    )
    audit_logs: Mapped[list["LogAuditoria"]] = relationship(
        back_populates="usuario", passive_deletes=True
    )


class SessaoAutenticacao(Base):
    __tablename__ = "sessoes_autenticacao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    usuario: Mapped[Usuario] = relationship(back_populates="sessions")


class LogAuditoria(Base):
    __tablename__ = "logs_auditoria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True, index=True
    )
    acao: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entidade: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entidade_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    usuario: Mapped[Usuario | None] = relationship(back_populates="audit_logs")
