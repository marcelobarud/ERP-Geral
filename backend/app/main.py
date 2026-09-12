import os

from dotenv import dotenv_values
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.appearance import LOGO_STORAGE_DIR
from app.api.appearance import router as appearance_router
from app.api.audit import router as audit_router
from app.api.auth import router as auth_router
from app.api.catalog import router as catalog_router
from app.api.commercial import router as commercial_router
from app.api.custom_fields import router as custom_fields_router
from app.api.customers import router as customers_router
from app.api.dashboard import router as dashboard_router
from app.api.employees import router as employees_router
from app.api.finance import router as finance_router
from app.api.health import router as health_router
from app.api.inventory import router as inventory_router
from app.api.modules import router as modules_router
from app.api.products import router as products_router
from app.api.purchases import router as purchases_router
from app.api.reports import router as reports_router
from app.api.sales import router as sales_router
from app.api.suppliers import router as suppliers_router
from app.api.system import router as system_router
from app.api.users import router as users_router
from app.core.config import PROJECT_ROOT
from app.core.errors import register_exception_handlers

_PUBLIC_ENV_VALUES = dotenv_values(PROJECT_ROOT / ".env")


def _runtime_env(name: str, default: str = "") -> str:
    return os.getenv(name) or str(_PUBLIC_ENV_VALUES.get(name) or default)


def _runtime_bool(name: str, default: bool) -> bool:
    value = _runtime_env(name)
    if not value:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "sim"}


def _cors_origins() -> list[str]:
    configured = [
        origin.strip()
        for origin in _runtime_env("CORS_ORIGINS").split(",")
        if origin.strip()
    ]
    if configured:
        return configured
    if _runtime_env("ENVIRONMENT", "development").strip().lower() == "production":
        return []
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://192.168.1.107:5174",
    ]


def create_app() -> FastAPI:
    production = (
        _runtime_env("ENVIRONMENT", "development").strip().lower() == "production"
    )
    docs_enabled = _runtime_bool("API_DOCS_ENABLED", not production)
    application = FastAPI(
        title="ERP Geral",
        version="0.1.0",
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )

    @application.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )
        response.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
        )
        return response

    application.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Accept", "Authorization", "Content-Type"],
    )
    register_exception_handlers(application)
    application.include_router(health_router)
    application.include_router(system_router)
    application.include_router(auth_router)
    application.include_router(users_router)
    application.include_router(audit_router)
    application.include_router(catalog_router)
    application.include_router(commercial_router)
    LOGO_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    application.mount(
        "/uploads",
        StaticFiles(directory=LOGO_STORAGE_DIR.parent),
        name="uploads",
    )
    application.include_router(appearance_router)
    application.include_router(custom_fields_router)
    application.include_router(customers_router)
    application.include_router(dashboard_router)
    application.include_router(suppliers_router)
    application.include_router(employees_router)
    application.include_router(products_router)
    application.include_router(sales_router)
    application.include_router(inventory_router)
    application.include_router(purchases_router)
    application.include_router(finance_router)
    application.include_router(reports_router)
    application.include_router(modules_router)
    return application


app = create_app()
