"""Configuração persistente da identidade visual do ERP."""

from sqlalchemy import JSON, CheckConstraint, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AppearanceSettings(Base):
    __tablename__ = "configuracoes_aparencia"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome_sistema: Mapped[str] = mapped_column(String(120), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cor_primaria: Mapped[str] = mapped_column(String(7), nullable=False)
    cor_secundaria: Mapped[str] = mapped_column(String(7), nullable=False)
    cor_destaque: Mapped[str] = mapped_column(String(7), nullable=False)
    cor_fundo: Mapped[str] = mapped_column(String(7), nullable=False)
    cor_superficie: Mapped[str] = mapped_column(String(7), nullable=False)
    cor_texto: Mapped[str] = mapped_column(String(7), nullable=False)
    cor_texto_primario: Mapped[str] = mapped_column(String(7), nullable=False)
    cor_texto_secundario: Mapped[str] = mapped_column(String(7), nullable=False)
    cor_texto_mudo: Mapped[str] = mapped_column(String(7), nullable=False)
    cor_titulo: Mapped[str] = mapped_column(String(7), nullable=False)
    cor_link: Mapped[str] = mapped_column(String(7), nullable=False)
    cor_sobre_primaria: Mapped[str] = mapped_column(String(7), nullable=False)
    cor_sobre_secundaria: Mapped[str] = mapped_column(String(7), nullable=False)
    cor_sobre_destaque: Mapped[str] = mapped_column(String(7), nullable=False)
    cor_tabela_cabecalho: Mapped[str] = mapped_column(String(7), nullable=False)
    cor_tabela_corpo: Mapped[str] = mapped_column(String(7), nullable=False)
    cor_tabela_fundo: Mapped[str] = mapped_column(String(7), nullable=False)
    cor_tabela_borda: Mapped[str] = mapped_column(String(7), nullable=False)
    cor_perigo: Mapped[str] = mapped_column(String(7), nullable=False)
    cor_sucesso: Mapped[str] = mapped_column(String(7), nullable=False)
    cor_aviso: Mapped[str] = mapped_column(String(7), nullable=False)
    raio_controle: Mapped[str] = mapped_column(String(20), nullable=False)
    raio_card: Mapped[str] = mapped_column(String(20), nullable=False)
    rotulo_dashboard: Mapped[str] = mapped_column(String(80), nullable=False)
    rotulo_clientes: Mapped[str] = mapped_column(String(80), nullable=False)
    rotulo_produtos: Mapped[str] = mapped_column(String(80), nullable=False)
    rotulo_funcionarios: Mapped[str] = mapped_column(String(80), nullable=False)
    rotulo_fornecedores: Mapped[str] = mapped_column(String(80), nullable=False)
    rotulo_vendas: Mapped[str] = mapped_column(String(80), nullable=False)
    rotulo_nova_venda: Mapped[str] = mapped_column(String(80), nullable=False)


class PageAppearanceSettings(Base):
    __tablename__ = "configuracoes_aparencia_paginas"
    __table_args__ = (
        UniqueConstraint("pagina", name="uq_config_aparencia_paginas_pagina"),
        CheckConstraint(
            "pagina IN ('dashboard', 'customers', 'products', 'employees', "
            "'suppliers', 'sales', 'new_sale', 'settings', "
            "'reports_dashboard', 'reports_commercial', 'reports_purchases', "
            "'reports_stock', 'reports_finance')",
            name="ck_config_aparencia_paginas_pagina",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pagina: Mapped[str] = mapped_column(String(32), nullable=False)
    cor_fundo: Mapped[str | None] = mapped_column(String(7), nullable=True)
    cor_superficie: Mapped[str | None] = mapped_column(String(7), nullable=True)
    cor_titulo: Mapped[str | None] = mapped_column(String(7), nullable=True)
    cor_texto_primario: Mapped[str | None] = mapped_column(String(7), nullable=True)
    cor_texto_secundario: Mapped[str | None] = mapped_column(String(7), nullable=True)
    cor_texto_mudo: Mapped[str | None] = mapped_column(String(7), nullable=True)
    cor_destaque: Mapped[str | None] = mapped_column(String(7), nullable=True)
    cor_link: Mapped[str | None] = mapped_column(String(7), nullable=True)


class ElementAppearanceOverride(Base):
    """Override visual tipado de um elemento identificado pela aplicação."""

    __tablename__ = "configuracoes_aparencia_elementos"
    __table_args__ = (
        UniqueConstraint(
            "customization_key",
            name="uq_config_aparencia_elementos_key",
        ),
        CheckConstraint(
            "customization_type IN ("
            "'TEXT', 'SURFACE', 'BUTTON', 'INPUT', 'TABLE', 'PAGE')",
            name="ck_config_aparencia_elementos_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customization_key: Mapped[str] = mapped_column(String(120), nullable=False)
    customization_type: Mapped[str] = mapped_column(String(16), nullable=False)
    customization_group: Mapped[str | None] = mapped_column(String(80), nullable=True)
    pagina: Mapped[str | None] = mapped_column(String(32), nullable=True)
    properties: Mapped[dict[str, str | int]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
