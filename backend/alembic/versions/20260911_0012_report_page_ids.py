"""Separa identificadores visuais dos relatórios."""

from collections.abc import Sequence

from alembic import op

revision: str = "20260911_0012"
down_revision: str | None = "20260911_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PAGE_IDS = (
    "'dashboard', 'customers', 'products', 'employees', 'suppliers', "
    "'sales', 'new_sale', 'settings', 'reports_dashboard', "
    "'reports_commercial', 'reports_purchases', 'reports_stock', "
    "'reports_finance'"
)


def upgrade() -> None:
    op.drop_constraint(
        "ck_config_aparencia_paginas_pagina",
        "configuracoes_aparencia_paginas",
        type_="check",
    )
    op.create_check_constraint(
        "ck_config_aparencia_paginas_pagina",
        "configuracoes_aparencia_paginas",
        f"pagina IN ({PAGE_IDS})",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_config_aparencia_paginas_pagina",
        "configuracoes_aparencia_paginas",
        type_="check",
    )
    op.create_check_constraint(
        "ck_config_aparencia_paginas_pagina",
        "configuracoes_aparencia_paginas",
        "pagina IN ('dashboard', 'customers', 'products', 'employees', "
        "'suppliers', 'sales', 'new_sale', 'settings')",
    )
