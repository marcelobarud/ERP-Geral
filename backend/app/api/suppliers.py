from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import require_authenticated, require_permission
from app.db.session import get_db_session
from app.models import Fornecedor, Produto, VendaItem
from app.schemas.pagination import PaginationResponse
from app.schemas.suppliers import (
    FornecedorCreate,
    FornecedorDetailRead,
    FornecedorProdutoRead,
    FornecedorRead,
    FornecedorUpdate,
)
from app.services.custom_fields import (
    CUSTOM_FIELD_DOMAINS,
    CustomFieldValidationError,
    apply_values,
    read_values,
)
from app.services.pagination import paginate

router = APIRouter(
    prefix="/api/suppliers",
    tags=["suppliers"],
    dependencies=[Depends(require_authenticated)],
)


def ensure_unique_cnpj(
    db: Session,
    cnpj: str,
    supplier_id: int | None = None,
) -> None:
    query = select(Fornecedor).where(Fornecedor.cnpj == cnpj)
    if supplier_id is not None:
        query = query.where(Fornecedor.id != supplier_id)
    if db.scalar(query) is not None:
        raise HTTPException(status_code=409, detail="CNPJ já cadastrado.")


@router.get("", response_model=PaginationResponse[FornecedorRead])
def list_suppliers(
    search: str | None = Query(default=None),
    city: str | None = Query(default=None),
    state: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db_session),
) -> PaginationResponse[FornecedorRead]:
    query = select(Fornecedor)
    normalized_search = search.strip() if search else ""
    normalized_city = city.strip() if city else ""
    normalized_state = state.strip() if state else ""
    if normalized_search:
        pattern = f"%{normalized_search}%"
        query = query.where(
            or_(
                Fornecedor.nome.ilike(pattern),
                Fornecedor.cnpj.ilike(pattern),
                Fornecedor.cidade.ilike(pattern),
                Fornecedor.estado.ilike(pattern),
            )
        )
    if normalized_city:
        query = query.where(Fornecedor.cidade.ilike(normalized_city))
    if normalized_state:
        query = query.where(Fornecedor.estado.ilike(normalized_state))
    items, total, total_pages = paginate(
        db, query.order_by(Fornecedor.id), page, page_size
    )
    return PaginationResponse[FornecedorRead](
        items=list(items),
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.get("/{supplier_id}", response_model=FornecedorDetailRead)
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db_session),
) -> FornecedorDetailRead:
    supplier = db.scalar(
        select(Fornecedor)
        .options(selectinload(Fornecedor.produtos))
        .where(Fornecedor.id == supplier_id)
    )
    if supplier is None:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado.")

    supplier_read = FornecedorRead.model_validate(supplier)
    supplier_read = FornecedorRead(
        **FornecedorRead.model_validate(supplier).model_dump(
            exclude={"campos_personalizados"}
        ),
        campos_personalizados=read_values(
            db, CUSTOM_FIELD_DOMAINS["suppliers"], supplier.id
        ),
    )
    return FornecedorDetailRead(
        **supplier_read.model_dump(),
        produtos=[
            FornecedorProdutoRead.model_validate(product)
            for product in supplier.produtos
        ],
    )


@router.post(
    "",
    response_model=FornecedorRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("suppliers:write"))],
)
def create_supplier(
    payload: FornecedorCreate,
    db: Session = Depends(get_db_session),
) -> Fornecedor:
    ensure_unique_cnpj(db, payload.cnpj)
    custom_values = payload.campos_personalizados
    supplier = Fornecedor(**payload.model_dump(exclude={"campos_personalizados"}))
    db.add(supplier)
    try:
        db.flush()
        apply_values(db, CUSTOM_FIELD_DOMAINS["suppliers"], supplier.id, custom_values)
        db.commit()
    except CustomFieldValidationError as exception:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exception)) from None
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="CNPJ já cadastrado.") from None
    db.refresh(supplier)
    return FornecedorRead(
        **FornecedorRead.model_validate(supplier).model_dump(
            exclude={"campos_personalizados"}
        ),
        campos_personalizados=read_values(
            db, CUSTOM_FIELD_DOMAINS["suppliers"], supplier.id
        ),
    )


@router.patch(
    "/{supplier_id}",
    response_model=FornecedorRead,
    dependencies=[Depends(require_permission("suppliers:write"))],
)
def update_supplier(
    supplier_id: int,
    payload: FornecedorUpdate,
    db: Session = Depends(get_db_session),
) -> Fornecedor:
    supplier = db.get(Fornecedor, supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado.")

    updates = payload.model_dump(exclude_unset=True)
    custom_values = updates.pop("campos_personalizados", None)
    if "cnpj" in updates:
        ensure_unique_cnpj(db, updates["cnpj"], supplier_id)
    for field_name, value in updates.items():
        setattr(supplier, field_name, value)
    try:
        db.flush()
        apply_values(
            db,
            CUSTOM_FIELD_DOMAINS["suppliers"],
            supplier.id,
            custom_values or {},
        )
        db.commit()
    except CustomFieldValidationError as exception:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exception)) from None
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="CNPJ já cadastrado.") from None
    db.refresh(supplier)
    return FornecedorRead(
        **FornecedorRead.model_validate(supplier).model_dump(
            exclude={"campos_personalizados"}
        ),
        campos_personalizados=read_values(
            db, CUSTOM_FIELD_DOMAINS["suppliers"], supplier.id
        ),
    )


@router.delete(
    "/{supplier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("suppliers:write"))],
)
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db_session),
) -> Response:
    supplier = db.get(Fornecedor, supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado.")
    has_products = db.scalar(
        select(Produto.id).where(Produto.fornecedor_id == supplier_id)
    )
    if has_products is not None:
        raise HTTPException(
            status_code=409,
            detail="Fornecedor possui produtos relacionados e não pode ser excluído.",
        )
    has_historical_sales = db.scalar(
        select(VendaItem.id).where(VendaItem.fornecedor_id == supplier_id)
    )
    if has_historical_sales is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Fornecedor possui vendas históricas relacionadas e não pode "
                "ser excluído."
            ),
        )
    db.delete(supplier)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "Fornecedor possui produtos ou vendas históricas relacionadas "
                "e não pode ser excluído."
            ),
        ) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
