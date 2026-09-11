from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models import Fornecedor, Produto, VendaItem
from app.schemas.pagination import PaginationResponse
from app.schemas.products import ProdutoCreate, ProdutoRead, ProdutoUpdate
from app.services.custom_fields import (
    CUSTOM_FIELD_DOMAINS,
    CustomFieldValidationError,
    apply_values,
    read_values,
)
from app.services.pagination import paginate

router = APIRouter(prefix="/api/products", tags=["products"])


def ensure_supplier_exists(db: Session, supplier_id: int) -> None:
    if db.get(Fornecedor, supplier_id) is None:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado.")


@router.get("", response_model=PaginationResponse[ProdutoRead])
def list_products(
    search: str | None = Query(default=None),
    category: str | None = Query(default=None),
    supplier_id: int | None = Query(default=None, gt=0),
    cost_min: Decimal | None = Query(default=None, ge=0),
    cost_max: Decimal | None = Query(default=None, ge=0),
    sale_price_min: Decimal | None = Query(default=None, ge=0),
    sale_price_max: Decimal | None = Query(default=None, ge=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db_session),
) -> PaginationResponse[ProdutoRead]:
    if cost_min is not None and cost_max is not None and cost_min > cost_max:
        raise HTTPException(
            status_code=422,
            detail="O preço de custo mínimo não pode ser maior que o máximo.",
        )
    if (
        sale_price_min is not None
        and sale_price_max is not None
        and sale_price_min > sale_price_max
    ):
        raise HTTPException(
            status_code=422,
            detail="O preço de venda mínimo não pode ser maior que o máximo.",
        )

    query = select(Produto)
    normalized_search = search.strip() if search else ""
    normalized_category = category.strip() if category else ""
    if normalized_search:
        pattern = f"%{normalized_search}%"
        query = query.where(
            or_(
                Produto.nome.ilike(pattern),
                Produto.categoria.ilike(pattern),
                Produto.fornecedor.has(Fornecedor.nome.ilike(pattern)),
            )
        )
    if normalized_category:
        query = query.where(Produto.categoria.ilike(normalized_category))
    if supplier_id is not None:
        query = query.where(Produto.fornecedor_id == supplier_id)
    if cost_min is not None:
        query = query.where(Produto.preco_custo >= cost_min)
    if cost_max is not None:
        query = query.where(Produto.preco_custo <= cost_max)
    if sale_price_min is not None:
        query = query.where(Produto.preco_venda >= sale_price_min)
    if sale_price_max is not None:
        query = query.where(Produto.preco_venda <= sale_price_max)
    items, total, total_pages = paginate(
        db, query.order_by(Produto.id), page, page_size
    )
    return PaginationResponse[ProdutoRead](
        items=list(items),
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.get("/{product_id}", response_model=ProdutoRead)
def get_product(product_id: int, db: Session = Depends(get_db_session)) -> Produto:
    product = db.get(Produto, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return ProdutoRead(
        **ProdutoRead.model_validate(product).model_dump(
            exclude={"campos_personalizados"}
        ),
        campos_personalizados=read_values(
            db, CUSTOM_FIELD_DOMAINS["products"], product.id
        ),
    )


@router.post("", response_model=ProdutoRead, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProdutoCreate,
    db: Session = Depends(get_db_session),
) -> Produto:
    ensure_supplier_exists(db, payload.fornecedor_id)
    custom_values = payload.campos_personalizados
    product = Produto(**payload.model_dump(exclude={"campos_personalizados"}))
    db.add(product)
    try:
        db.flush()
        apply_values(db, CUSTOM_FIELD_DOMAINS["products"], product.id, custom_values)
        db.commit()
    except CustomFieldValidationError as exception:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exception)) from None
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Não foi possível criar o produto por conflito de integridade.",
        ) from None
    db.refresh(product)
    return ProdutoRead(
        **ProdutoRead.model_validate(product).model_dump(
            exclude={"campos_personalizados"}
        ),
        campos_personalizados=read_values(
            db, CUSTOM_FIELD_DOMAINS["products"], product.id
        ),
    )


@router.patch("/{product_id}", response_model=ProdutoRead)
def update_product(
    product_id: int,
    payload: ProdutoUpdate,
    db: Session = Depends(get_db_session),
) -> Produto:
    product = db.get(Produto, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    updates = payload.model_dump(exclude_unset=True)
    custom_values = updates.pop("campos_personalizados", None)
    if "fornecedor_id" in updates:
        ensure_supplier_exists(db, updates["fornecedor_id"])
    for field_name, value in updates.items():
        setattr(product, field_name, value)
    try:
        db.flush()
        apply_values(
            db,
            CUSTOM_FIELD_DOMAINS["products"],
            product.id,
            custom_values or {},
        )
        db.commit()
    except CustomFieldValidationError as exception:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exception)) from None
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Não foi possível atualizar o produto por conflito de integridade.",
        ) from None
    db.refresh(product)
    return ProdutoRead(
        **ProdutoRead.model_validate(product).model_dump(
            exclude={"campos_personalizados"}
        ),
        campos_personalizados=read_values(
            db, CUSTOM_FIELD_DOMAINS["products"], product.id
        ),
    )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db_session)) -> Response:
    product = db.get(Produto, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    if (
        db.scalar(select(VendaItem.id).where(VendaItem.produto_id == product_id))
        is not None
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Produto possui itens de venda relacionados e não pode ser excluído."
            ),
        )
    db.delete(product)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "Produto possui itens de venda relacionados e não pode ser excluído."
            ),
        ) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
