from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import require_permission
from app.db.session import get_db_session
from app.models import LogAuditoria, Usuario
from app.schemas.auth import AuditLogRead

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])


@router.get("", response_model=list[AuditLogRead])
def list_audit_logs(
    db: Session = Depends(get_db_session),
    _: Usuario | None = Depends(require_permission("audit:read")),
) -> list[AuditLogRead]:
    logs = db.scalars(
        select(LogAuditoria).order_by(
            LogAuditoria.created_at.desc(), LogAuditoria.id.desc()
        )
    ).all()
    return [AuditLogRead.model_validate(log) for log in logs]
