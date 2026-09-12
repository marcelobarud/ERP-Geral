from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import require_authenticated
from app.api.health import _expected_migration
from app.core.config import get_settings
from app.core.version import PRODUCT_NAME, PRODUCT_VERSION
from app.db.session import get_db_session
from app.models import Usuario

router = APIRouter(
    prefix="/api",
    tags=["technical"],
    dependencies=[Depends(require_authenticated)],
)


@router.get("/system-info")
def system_info(
    db: Session = Depends(get_db_session),
    _: Usuario | None = Depends(require_authenticated),
) -> dict[str, str | None]:
    current_migration = db.execute(
        text("SELECT version_num FROM alembic_version")
    ).scalar_one_or_none()
    expected_migration = _expected_migration()
    return {
        "product": PRODUCT_NAME,
        "version": PRODUCT_VERSION,
        "environment": get_settings().environment,
        "current_migration": current_migration,
        "expected_migration": expected_migration,
        "schema": "ok" if current_migration == expected_migration else "outdated",
    }
