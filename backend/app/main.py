from fastapi import FastAPI
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
from app.api.health import router as health_router
from app.api.inventory import router as inventory_router
from app.api.products import router as products_router
from app.api.purchases import router as purchases_router
from app.api.sales import router as sales_router
from app.api.suppliers import router as suppliers_router
from app.api.users import router as users_router
from app.core.errors import register_exception_handlers


def create_app() -> FastAPI:
    application = FastAPI(title="ERP Geral", version="0.1.0")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://192.168.1.107:5174",
        ],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Accept", "Authorization", "Content-Type"],
    )
    register_exception_handlers(application)
    application.include_router(health_router)
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
    return application


app = create_app()
