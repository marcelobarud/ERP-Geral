from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import get_engine

router = APIRouter(prefix="/api", tags=["technical"])


@router.get("/health")
def health_check() -> dict[str, str | None]:
    expected_migration = _expected_migration()
    result: dict[str, str | None] = {
        "status": "ok",
        "process": "ok",
        "database": "ok",
        "schema": "ok",
        "current_migration": None,
        "expected_migration": expected_migration,
    }

    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
            current_migration = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one_or_none()
            result["current_migration"] = current_migration
    except Exception:
        result.update(
            status="degraded",
            database="offline",
            schema="unknown",
        )
        return result

    if result["current_migration"] != expected_migration:
        result.update(status="degraded", schema="outdated")

    return result


def _expected_migration() -> str | None:
    try:
        backend_root = Path(__file__).resolve().parents[2]
        config = Config(str(backend_root / "alembic.ini"))
        heads = ScriptDirectory.from_config(config).get_heads()
        return heads[0] if len(heads) == 1 else ",".join(heads)
    except Exception:
        return None
