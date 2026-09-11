from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import require_authenticated, require_permission
from app.db.session import get_db_session
from app.schemas.custom_fields import (
    CustomFieldDefinitionCreate,
    CustomFieldDefinitionRead,
    CustomFieldDefinitionUpdate,
)
from app.services.custom_fields import (
    CUSTOM_FIELD_DOMAINS,
    CustomFieldValidationError,
    create_definition,
    list_definitions,
    update_definition,
)

router = APIRouter(
    prefix="/api/settings/custom-fields",
    tags=["custom-fields"],
    dependencies=[Depends(require_authenticated)],
)


def _list(domain_name: str, db: Session) -> list[dict[str, Any]]:
    return list_definitions(db, CUSTOM_FIELD_DOMAINS[domain_name])


def _create(domain_name: str, payload: CustomFieldDefinitionCreate, db: Session):
    try:
        result = create_definition(db, CUSTOM_FIELD_DOMAINS[domain_name], payload)
        db.commit()
        return result
    except CustomFieldValidationError as exception:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exception)) from None
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Já existe um campo com esse nome."
        ) from None


def _update(
    domain_name: str,
    field_id: int,
    payload: CustomFieldDefinitionUpdate,
    db: Session,
):
    try:
        result = update_definition(
            db, CUSTOM_FIELD_DOMAINS[domain_name], field_id, payload
        )
        db.commit()
        return result
    except CustomFieldValidationError as exception:
        db.rollback()
        message = str(exception)
        status_code = 404 if "não encontrado" in message else 422
        raise HTTPException(status_code=status_code, detail=message) from None
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Já existe um campo com esse nome."
        ) from None


@router.get("/customers", response_model=list[CustomFieldDefinitionRead])
def list_customer_fields(db: Session = Depends(get_db_session)):
    return _list("customers", db)


@router.post(
    "/customers",
    response_model=CustomFieldDefinitionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("settings:write"))],
)
def create_customer_field(
    payload: CustomFieldDefinitionCreate, db: Session = Depends(get_db_session)
):
    return _create("customers", payload, db)


@router.patch(
    "/customers/{field_id}",
    response_model=CustomFieldDefinitionRead,
    dependencies=[Depends(require_permission("settings:write"))],
)
def update_customer_field(
    field_id: int,
    payload: CustomFieldDefinitionUpdate,
    db: Session = Depends(get_db_session),
):
    return _update("customers", field_id, payload, db)


@router.get("/products", response_model=list[CustomFieldDefinitionRead])
def list_product_fields(db: Session = Depends(get_db_session)):
    return _list("products", db)


@router.post(
    "/products",
    response_model=CustomFieldDefinitionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("settings:write"))],
)
def create_product_field(
    payload: CustomFieldDefinitionCreate, db: Session = Depends(get_db_session)
):
    return _create("products", payload, db)


@router.patch(
    "/products/{field_id}",
    response_model=CustomFieldDefinitionRead,
    dependencies=[Depends(require_permission("settings:write"))],
)
def update_product_field(
    field_id: int,
    payload: CustomFieldDefinitionUpdate,
    db: Session = Depends(get_db_session),
):
    return _update("products", field_id, payload, db)


@router.get("/employees", response_model=list[CustomFieldDefinitionRead])
def list_employee_fields(db: Session = Depends(get_db_session)):
    return _list("employees", db)


@router.post(
    "/employees",
    response_model=CustomFieldDefinitionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("settings:write"))],
)
def create_employee_field(
    payload: CustomFieldDefinitionCreate, db: Session = Depends(get_db_session)
):
    return _create("employees", payload, db)


@router.patch(
    "/employees/{field_id}",
    response_model=CustomFieldDefinitionRead,
    dependencies=[Depends(require_permission("settings:write"))],
)
def update_employee_field(
    field_id: int,
    payload: CustomFieldDefinitionUpdate,
    db: Session = Depends(get_db_session),
):
    return _update("employees", field_id, payload, db)


@router.get("/suppliers", response_model=list[CustomFieldDefinitionRead])
def list_supplier_fields(db: Session = Depends(get_db_session)):
    return _list("suppliers", db)


@router.post(
    "/suppliers",
    response_model=CustomFieldDefinitionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("settings:write"))],
)
def create_supplier_field(
    payload: CustomFieldDefinitionCreate, db: Session = Depends(get_db_session)
):
    return _create("suppliers", payload, db)


@router.patch(
    "/suppliers/{field_id}",
    response_model=CustomFieldDefinitionRead,
    dependencies=[Depends(require_permission("settings:write"))],
)
def update_supplier_field(
    field_id: int,
    payload: CustomFieldDefinitionUpdate,
    db: Session = Depends(get_db_session),
):
    return _update("suppliers", field_id, payload, db)
