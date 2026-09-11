from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db_session
from app.models import Usuario
from app.services.auth import (
    InactiveUserError,
    has_permission,
    user_from_token,
)


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db_session),
) -> Usuario | None:
    settings = get_settings()
    if not settings.auth_required:
        return None
    token = _bearer_token(authorization)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user = user_from_token(db, token)
    except InactiveUserError:
        user = None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida ou expirada.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_authenticated(
    user: Usuario | None = Depends(get_current_user),
) -> Usuario | None:
    return user


def require_permission(permission: str) -> Callable:
    def dependency(
        user: Usuario | None = Depends(get_current_user),
    ) -> Usuario | None:
        if user is not None and not has_permission(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não possui permissão para esta operação.",
            )
        return user

    return dependency
