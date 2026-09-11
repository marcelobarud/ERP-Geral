import re
from typing import Literal

from pydantic import Field, model_validator

from app.schemas.base import APIModel, ReadModel

COLOR_PATTERN = r"^#[0-9A-Fa-f]{6}$"
RADIUS_PATTERN = r"^(0|[0-9]+(?:\.[0-9]+)?)(px|rem|em)$"


class AppearanceRead(ReadModel):
    id: int
    nome_sistema: str
    logo_url: str | None
    cor_primaria: str
    cor_secundaria: str
    cor_destaque: str
    cor_fundo: str
    cor_superficie: str
    cor_texto: str
    cor_texto_primario: str
    cor_texto_secundario: str
    cor_texto_mudo: str
    cor_titulo: str
    cor_link: str
    cor_sobre_primaria: str
    cor_sobre_secundaria: str
    cor_sobre_destaque: str
    cor_tabela_cabecalho: str
    cor_tabela_corpo: str
    cor_tabela_fundo: str
    cor_tabela_borda: str
    cor_perigo: str
    cor_sucesso: str
    cor_aviso: str
    raio_controle: str
    raio_card: str
    rotulo_dashboard: str
    rotulo_clientes: str
    rotulo_produtos: str
    rotulo_funcionarios: str
    rotulo_fornecedores: str
    rotulo_vendas: str
    rotulo_nova_venda: str


class AppearancePatch(APIModel):
    nome_sistema: str | None = Field(default=None, min_length=1, max_length=120)
    cor_primaria: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_secundaria: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_destaque: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_fundo: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_superficie: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_texto: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_texto_primario: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_texto_secundario: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_texto_mudo: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_titulo: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_link: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_sobre_primaria: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_sobre_secundaria: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_sobre_destaque: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_tabela_cabecalho: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_tabela_corpo: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_tabela_fundo: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_tabela_borda: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_perigo: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_sucesso: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_aviso: str | None = Field(default=None, pattern=COLOR_PATTERN)
    raio_controle: str | None = Field(
        default=None,
        pattern=RADIUS_PATTERN,
        max_length=20,
    )
    raio_card: str | None = Field(default=None, pattern=RADIUS_PATTERN, max_length=20)
    rotulo_dashboard: str | None = Field(default=None, min_length=1, max_length=80)
    rotulo_clientes: str | None = Field(default=None, min_length=1, max_length=80)
    rotulo_produtos: str | None = Field(default=None, min_length=1, max_length=80)
    rotulo_funcionarios: str | None = Field(default=None, min_length=1, max_length=80)
    rotulo_fornecedores: str | None = Field(default=None, min_length=1, max_length=80)
    rotulo_vendas: str | None = Field(default=None, min_length=1, max_length=80)
    rotulo_nova_venda: str | None = Field(default=None, min_length=1, max_length=80)


PageId = Literal[
    "dashboard",
    "customers",
    "products",
    "employees",
    "suppliers",
    "sales",
    "new_sale",
    "settings",
    "reports_dashboard",
    "reports_commercial",
    "reports_purchases",
    "reports_stock",
    "reports_finance",
]

CustomizationType = Literal[
    "TEXT",
    "SURFACE",
    "BUTTON",
    "INPUT",
    "TABLE",
    "PAGE",
]

CUSTOMIZATION_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]{2,119}$")
ELEMENT_PROPERTY_FIELDS: dict[str, set[str]] = {
    "TEXT": {"cor", "peso", "tamanho"},
    "SURFACE": {"cor_fundo", "cor_borda", "raio"},
    "BUTTON": {"cor_fundo", "cor_texto", "cor_borda", "raio"},
    "INPUT": {"cor_fundo", "cor_texto", "cor_borda", "raio"},
    "TABLE": {
        "cor_cabecalho",
        "cor_texto_cabecalho",
        "cor_corpo",
        "cor_texto_corpo",
        "cor_borda",
    },
    "PAGE": {"cor_fundo"},
}
COLOR_PROPERTIES = {
    "cor",
    "cor_fundo",
    "cor_borda",
    "cor_texto",
    "cor_cabecalho",
    "cor_texto_cabecalho",
    "cor_corpo",
    "cor_texto_corpo",
}


def _validate_customization_properties(
    customization_type: CustomizationType,
    properties: dict[str, str | int],
) -> dict[str, str | int]:
    allowed = ELEMENT_PROPERTY_FIELDS[customization_type]
    unknown = set(properties) - allowed
    if unknown:
        raise ValueError(
            "Propriedades não permitidas para o tipo "
            f"{customization_type}: {', '.join(sorted(unknown))}."
        )

    for property_name, value in properties.items():
        if property_name in COLOR_PROPERTIES:
            if not isinstance(value, str) or not re.fullmatch(COLOR_PATTERN, value):
                raise ValueError(
                    f"A propriedade {property_name} deve ser uma cor hexadecimal."
                )
        elif property_name == "peso":
            if not isinstance(value, int) or value not in {400, 500, 600, 700, 800}:
                raise ValueError(
                    "Peso deve ser uma das opções tipográficas permitidas."
                )
        elif property_name == "tamanho":
            if not isinstance(value, int) or not 12 <= value <= 36:
                raise ValueError("Tamanho deve estar entre 12 e 36 pixels.")
        elif property_name == "raio":
            if not isinstance(value, int) or not 0 <= value <= 24:
                raise ValueError("Arredondamento deve estar entre 0 e 24 pixels.")
    return properties


class AppearanceOverridePayload(APIModel):
    customization_type: CustomizationType
    customization_group: str | None = Field(default=None, max_length=80)
    pagina: PageId | None = None
    properties: dict[str, str | int]

    @staticmethod
    def validate_key(customization_key: str) -> str:
        if not CUSTOMIZATION_KEY_PATTERN.fullmatch(customization_key):
            raise ValueError("customization_key possui formato inválido.")
        return customization_key

    @model_validator(mode="after")
    def validate_properties(self) -> "AppearanceOverridePayload":
        _validate_customization_properties(self.customization_type, self.properties)
        return self


class AppearanceOverrideRead(ReadModel):
    id: int
    customization_key: str
    customization_type: CustomizationType
    customization_group: str | None
    pagina: PageId | None
    properties: dict[str, str | int]


class AppearanceOverridesRead(ReadModel):
    items: list[AppearanceOverrideRead]


class PageAppearancePatch(APIModel):
    cor_fundo: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_superficie: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_titulo: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_texto_primario: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_texto_secundario: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_texto_mudo: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_destaque: str | None = Field(default=None, pattern=COLOR_PATTERN)
    cor_link: str | None = Field(default=None, pattern=COLOR_PATTERN)


class PageAppearanceOverrideRead(PageAppearancePatch):
    pass


class ResolvedPageAppearance(ReadModel):
    cor_fundo: str
    cor_superficie: str
    cor_titulo: str
    cor_texto_primario: str
    cor_texto_secundario: str
    cor_texto_mudo: str
    cor_destaque: str
    cor_link: str


class PageAppearanceRead(ReadModel):
    pagina: PageId
    overrides: PageAppearanceOverrideRead
    resolved: ResolvedPageAppearance
    inherited: list[str]
