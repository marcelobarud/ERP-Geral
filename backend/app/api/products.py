import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import require_authenticated, require_permission
from app.db.session import get_db_session
from app.models import (
    CategoriaProduto,
    Fornecedor,
    HistoricoCustoProduto,
    Produto,
    ProdutoFornecedor,
    UnidadeMedida,
    VendaItem,
)
from app.schemas.pagination import PaginationResponse
from app.schemas.products import ProdutoCreate, ProdutoRead, ProdutoUpdate
from app.services.custom_fields import (
    CUSTOM_FIELD_DOMAINS,
    CustomFieldValidationError,
    apply_values,
    read_values,
)
from app.services.pagination import paginate

router = APIRouter(
    prefix="/api/products",
    tags=["products"],
    dependencies=[Depends(require_authenticated)],
)


def ensure_supplier_exists(db: Session, supplier_id: int) -> None:
    if db.get(Fornecedor, supplier_id) is None:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado.")


def ensure_category_exists(db: Session, category_id: int | None) -> None:
    if category_id is not None and db.get(CategoriaProduto, category_id) is None:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")


def ensure_unit_exists(db: Session, unit_code: str | None) -> None:
    if unit_code is not None and db.scalar(
        select(UnidadeMedida.id).where(
            UnidadeMedida.codigo == unit_code,
            UnidadeMedida.ativo.is_(True),
        )
    ) is None:
        raise HTTPException(status_code=422, detail="Unidade de medida inválida.")


def generate_sku() -> str:
    return f"ERP-{uuid.uuid4().hex[:12].upper()}"


def sync_primary_supplier(db: Session, product: Produto) -> None:
    db.query(ProdutoFornecedor).filter(
        ProdutoFornecedor.produto_id == product.id
    ).update({"preferencial": False}, synchronize_session=False)
    link = db.scalar(
        select(ProdutoFornecedor).where(
            ProdutoFornecedor.produto_id == product.id,
            ProdutoFornecedor.fornecedor_id == product.fornecedor_id,
        )
    )
    if link is None:
        db.add(
            ProdutoFornecedor(
                produto_id=product.id,
                fornecedor_id=product.fornecedor_id,
                custo_referencia=product.preco_custo,
                preferencial=True,
            )
        )
    else:
        link.preferencial = True
        link.ativo = True


@router.get("", response_model=PaginationResponse[ProdutoRead])
def list_products(
    search: str | None = Query(default=None),
    category: str | None = Query(default=None),
    supplier_id: int | None = Query(default=None, gt=0),
    active: bool | None = Query(default=None),
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
    if active is not None:
        query = query.where(Produto.ativo == active)
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


@router.post(
    "",
    response_model=ProdutoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("products:write"))],
)
def create_product(
    payload: ProdutoCreate,
    db: Session = Depends(get_db_session),
) -> Produto:
    ensure_supplier_exists(db, payload.fornecedor_id)
    ensure_category_exists(db, payload.categoria_id)
    ensure_unit_exists(db, payload.unidade_medida)
    custom_values = payload.campos_personalizados
    product_data = payload.model_dump(exclude={"campos_personalizados", "sku"})
    product = Produto(sku=payload.sku or generate_sku(), **product_data)
    db.add(product)
    try:
        db.flush()
        db.add(
            HistoricoCustoProduto(
                produto_id=product.id,
                fornecedor_id=product.fornecedor_id,
                custo=product.preco_custo,
                origem="produto_criado",
            )
        )
        sync_primary_supplier(db, product)
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


@router.patch(
    "/{product_id}",
    response_model=ProdutoRead,
    dependencies=[Depends(require_permission("products:write"))],
)
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
    ensure_category_exists(db, updates.get("categoria_id"))
    ensure_unit_exists(db, updates.get("unidade_medida"))
    previous_cost = product.preco_custo
    previous_supplier_id = product.fornecedor_id
    for field_name, value in updates.items():
        setattr(product, field_name, value)
    try:
        db.flush()
        if "preco_custo" in updates and updates["preco_custo"] != previous_cost:
            db.add(
                HistoricoCustoProduto(
                    produto_id=product.id,
                    fornecedor_id=product.fornecedor_id,
                    custo=product.preco_custo,
                    origem="produto_atualizado",
                )
            )
        if (
            "fornecedor_id" in updates
            and updates["fornecedor_id"] != previous_supplier_id
        ):
            sync_primary_supplier(db, product)
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


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("products:write"))],
)
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
