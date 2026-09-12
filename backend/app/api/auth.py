from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_authenticated
from app.core.config import get_settings
from app.core.rate_limit import bootstrap_rate_limit, login_rate_limit
from app.db.session import get_db_session
from app.models import Usuario
from app.schemas.auth import (
    AuthConfigRead,
    BootstrapStatusRead,
    BootstrapRequest,
    LoginRequest,
    LoginResponse,
    UsuarioRead,
)
from app.services.auth import (
    AuthenticationError,
    InactiveUserError,
    add_audit_log,
    authenticate_user,
    hash_password,
    issue_session,
    revoke_session,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_read(user: Usuario) -> UsuarioRead:
    return UsuarioRead.model_validate(user)


@router.get("/config", response_model=AuthConfigRead)
def auth_config() -> AuthConfigRead:
    return AuthConfigRead(auth_required=get_settings().auth_required)


@router.get("/bootstrap-status", response_model=BootstrapStatusRead)
def bootstrap_status(db: Session = Depends(get_db_session)) -> BootstrapStatusRead:
    return BootstrapStatusRead(
        available=db.scalar(select(func.count()).select_from(Usuario)) == 0
    )


@router.post("/bootstrap", response_model=LoginResponse, status_code=201)
def bootstrap(
    payload: BootstrapRequest,
    db: Session = Depends(get_db_session),
    _: None = Depends(bootstrap_rate_limit),
) -> LoginResponse:
    settings = get_settings()
    if db.scalar(select(func.count()).select_from(Usuario)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A configuração inicial já foi concluída.",
        )
    if settings.auth_bootstrap_token and payload.token != settings.auth_bootstrap_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token de configuração inicial inválido.",
        )
    if (
        settings.environment.strip().lower() == "production"
        and not settings.auth_bootstrap_token
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A configuração inicial segura não está disponível.",
        )

    user = Usuario(
        nome=payload.nome,
        email=payload.email,
        senha_hash=hash_password(payload.senha),
        role="ADMIN",
    )
    db.add(user)
    try:
        db.flush()
        add_audit_log(
            db,
            user_id=user.id,
            action="bootstrap",
            entity="usuario",
            entity_id=user.id,
        )
        token, expires_at = issue_session(db, user)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível criar o usuário inicial.",
        ) from None
    return LoginResponse(
        access_token=token,
        expires_at=expires_at,
        usuario=_user_read(user),
    )


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db_session),
    _: None = Depends(login_rate_limit),
) -> LoginResponse:
    try:
        user = authenticate_user(db, payload.email, payload.senha)
    except InactiveUserError as exception:
        raise HTTPException(status_code=403, detail=str(exception)) from None
    except AuthenticationError as exception:
        raise HTTPException(status_code=401, detail=str(exception)) from None

    try:
        token, expires_at = issue_session(db, user)
        add_audit_log(
            db,
            user_id=user.id,
            action="login",
            entity="sessao_autenticacao",
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return LoginResponse(
        access_token=token,
        expires_at=expires_at,
        usuario=_user_read(user),
    )


@router.get("/me", response_model=UsuarioRead)
def current_user(user: Usuario | None = Depends(get_current_user)) -> UsuarioRead:
    if user is None:
        raise HTTPException(status_code=401, detail="Autenticação necessária.")
    return _user_read(user)


@router.post("/logout")
def logout(
    authorization: str | None = Header(default=None),
    user: Usuario | None = Depends(require_authenticated),
    db: Session = Depends(get_db_session),
) -> dict[str, bool]:
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            revoke_session(db, token.strip())
    if user is not None:
        add_audit_log(
            db,
            user_id=user.id,
            action="logout",
            entity="sessao_autenticacao",
        )
    db.commit()
    return {"ok": True}
