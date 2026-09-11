"""Limites simples por processo para proteger endpoints sensíveis."""

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request, status

_BUCKETS: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_LOCK = Lock()


def _check(request: Request, scope: str, limit: int, window: float) -> None:
    client = request.client.host if request.client else "unknown"
    key = (scope, client)
    now = monotonic()
    with _LOCK:
        bucket = _BUCKETS[key]
        while bucket and now - bucket[0] >= window:
            bucket.popleft()
        if len(bucket) >= limit:
            retry_after = max(1, int(window - (now - bucket[0])))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas tentativas. Aguarde antes de tentar novamente.",
                headers={"Retry-After": str(retry_after)},
            )
        bucket.append(now)


def login_rate_limit(request: Request) -> None:
    _check(request, "login", 20, 60)


def bootstrap_rate_limit(request: Request) -> None:
    _check(request, "bootstrap", 5, 3600)


def upload_rate_limit(request: Request) -> None:
    _check(request, "branding-upload", 20, 60)
