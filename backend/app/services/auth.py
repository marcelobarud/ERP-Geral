"""Regras de autenticação, autorização e auditoria."""

import base64
import binascii
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models import LogAuditoria, SessaoAutenticacao, Usuario
from app.schemas.auth import UserRole

PASSWORD_ITERATIONS = 240_000

ROLE_PERMISSIONS: dict[UserRole, frozenset[str]] = {
    "ADMIN": frozenset({"*"}),
    "MANAGER": frozenset(
        {
            "read",
            "customers:write",
            "suppliers:write",
            "employees:write",
            "products:write",
            "commercial:write",
            "inventory:write",
            "purchases:write",
            "sales:create",
            "sales:cancel",
            "settings:write",
        }
    ),
    "OPERATOR": frozenset({"read", "sales:create"}),
}


class AuthenticationError(Exception):
    """Credenciais inválidas ou sessão não disponível."""


class InactiveUserError(Exception):
    """Usuário existente, porém desativado."""


class UserConflictError(Exception):
    """Dados de usuário já utilizados."""


class BootstrapDisabledError(Exception):
    """A criação inicial não está disponível."""


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, PASSWORD_ITERATIONS
    )
    encode = base64.urlsafe_b64encode
    return "pbkdf2_sha256${}${}${}".format(
        PASSWORD_ITERATIONS,
        encode(salt).decode(),
        encode(digest).decode(),
    )


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, iterations, salt_value, digest_value = encoded_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_value.encode())
        expected = base64.urlsafe_b64decode(digest_value.encode())
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt, int(iterations)
        )
    except (TypeError, ValueError):
        return False
    return hmac.compare_digest(actual, expected)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _encode_token(session_id: int, expires_at: datetime) -> str:
    settings = get_settings()
    if not settings.auth_secret:
        raise AuthenticationError("A autenticação não está configurada.")
    payload = json.dumps(
        {
            "sid": session_id,
            "exp": int(expires_at.timestamp()),
            "nonce": secrets.token_urlsafe(12),
        },
        separators=(",", ":"),
    ).encode()
    encoded_payload = base64.urlsafe_b64encode(payload).rstrip(b"=")
    signature = hmac.new(
        settings.auth_secret.encode(), encoded_payload, hashlib.sha256
    ).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).rstrip(b"=")
    return f"{encoded_payload.decode()}.{encoded_signature.decode()}"


def _decode_token(token: str) -> dict[str, int] | None:
    settings = get_settings()
    if not settings.auth_secret or token.count(".") != 1:
        return None
    encoded_payload, encoded_signature = token.split(".", 1)
    try:
        payload_bytes = encoded_payload.encode()
        expected_signature = hmac.new(
            settings.auth_secret.encode(), payload_bytes, hashlib.sha256
        ).digest()
        received_signature = base64.urlsafe_b64decode(
            encoded_signature.encode() + b"=" * (-len(encoded_signature) % 4)
        )
        if not hmac.compare_digest(received_signature, expected_signature):
            return None
        payload = json.loads(
            base64.urlsafe_b64decode(
                encoded_payload.encode() + b"=" * (-len(encoded_payload) % 4)
            )
        )
        if not isinstance(payload, dict):
            return None
        return {"sid": int(payload["sid"]), "exp": int(payload["exp"])}
    except (
        KeyError,
        TypeError,
        ValueError,
        binascii.Error,
        UnicodeDecodeError,
        OverflowError,
        json.JSONDecodeError,
    ):
        return None


def authenticate_user(db: Session, email: str, password: str) -> Usuario:
    user = db.scalar(select(Usuario).where(Usuario.email == email.strip().lower()))
    if user is None or not verify_password(password, user.senha_hash):
        raise AuthenticationError("E-mail ou senha inválidos.")
    if not user.ativo:
        raise InactiveUserError("O usuário está inativo.")
    return user


def issue_session(db: Session, user: Usuario) -> tuple[str, datetime]:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=get_settings().auth_token_expiration_minutes
    )
    session = SessaoAutenticacao(
        usuario_id=user.id,
        token_hash="pending",
        expires_at=expires_at,
    )
    db.add(session)
    db.flush()
    token = _encode_token(session.id, expires_at)
    session.token_hash = _token_hash(token)
    return token, expires_at


def revoke_session(db: Session, token: str) -> None:
    payload = _decode_token(token)
    if payload is None:
        return
    session = db.scalar(
        select(SessaoAutenticacao).where(
            SessaoAutenticacao.id == payload["sid"],
            SessaoAutenticacao.token_hash == _token_hash(token),
        )
    )
    if session is not None and session.revoked_at is None:
        session.revoked_at = datetime.now(timezone.utc)


def user_from_token(db: Session, token: str) -> Usuario | None:
    payload = _decode_token(token)
    if payload is None or payload["exp"] <= int(datetime.now(timezone.utc).timestamp()):
        return None
    session = db.scalar(
        select(SessaoAutenticacao)
        .options(selectinload(SessaoAutenticacao.usuario))
        .where(
            SessaoAutenticacao.id == payload["sid"],
            SessaoAutenticacao.token_hash == _token_hash(token),
            SessaoAutenticacao.revoked_at.is_(None),
        )
    )
    if session is None or session.expires_at <= datetime.now(timezone.utc):
        return None
    if not session.usuario.ativo:
        raise InactiveUserError("O usuário está inativo.")
    return session.usuario


def has_permission(user: Usuario, permission: str) -> bool:
    permissions = ROLE_PERMISSIONS.get(user.role, frozenset())
    return "*" in permissions or permission in permissions


def add_audit_log(
    db: Session,
    *,
    user_id: int | None,
    action: str,
    entity: str,
    entity_id: int | None = None,
    metadata: dict | None = None,
) -> LogAuditoria:
    entry = LogAuditoria(
        usuario_id=user_id,
        acao=action,
        entidade=entity,
        entidade_id=entity_id,
        metadata_json=metadata,
    )
    db.add(entry)
    return entry
