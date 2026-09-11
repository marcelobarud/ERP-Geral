from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import require_authenticated, require_permission
from app.db.session import get_db_session
from app.models import (
    CategoriaProduto,
    Fornecedor,
    Produto,
    ProdutoFornecedor,
    UnidadeMedida,
    Usuario,
)
from app.schemas.catalog import (
    CategoriaProdutoCreate,
    CategoriaProdutoRead,
    ProdutoFornecedorCreate,
    ProdutoFornecedorRead,
    UnidadeMedidaRead,
)

router = APIRouter(
    prefix="/api/catalog",
    tags=["catalog"],
    dependencies=[Depends(require_authenticated)],
)


@router.get("/categories", response_model=list[CategoriaProdutoRead])
def list_categories(
    db: Session = Depends(get_db_session),
) -> list[CategoriaProdutoRead]:
    categories = db.scalars(
        select(CategoriaProduto).where(CategoriaProduto.ativo.is_(True)).order_by(CategoriaProduto.nome)
    ).all()
    return [CategoriaProdutoRead.model_validate(category) for category in categories]


@router.post(
    "/categories",
    response_model=CategoriaProdutoRead,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    payload: CategoriaProdutoCreate,
    db: Session = Depends(get_db_session),
    _: Usuario | None = Depends(require_permission("products:write")),
) -> CategoriaProdutoRead:
    category = CategoriaProduto(nome=payload.nome)
    db.add(category)
    try:
        db.commit()
        db.refresh(category)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Categoria já cadastrada."
        ) from None
    return CategoriaProdutoRead.model_validate(category)


@router.get("/units", response_model=list[UnidadeMedidaRead])
def list_units(db: Session = Depends(get_db_session)) -> list[UnidadeMedidaRead]:
    units = db.scalars(
        select(UnidadeMedida).where(UnidadeMedida.ativo.is_(True)).order_by(UnidadeMedida.codigo)
    ).all()
    return [UnidadeMedidaRead.model_validate(unit) for unit in units]


@router.get(
    "/products/{product_id}/suppliers",
    response_model=list[ProdutoFornecedorRead],
)
def list_product_suppliers(
    product_id: int,
    db: Session = Depends(get_db_session),
) -> list[ProdutoFornecedorRead]:
    if db.get(Produto, product_id) is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    links = db.scalars(
        select(ProdutoFornecedor)
        .where(ProdutoFornecedor.produto_id == product_id)
        .order_by(ProdutoFornecedor.preferencial.desc(), ProdutoFornecedor.id)
    ).all()
    return [ProdutoFornecedorRead.model_validate(link) for link in links]


@router.post(
    "/products/{product_id}/suppliers",
    response_model=ProdutoFornecedorRead,
    status_code=status.HTTP_201_CREATED,
)
def add_product_supplier(
    product_id: int,
    payload: ProdutoFornecedorCreate,
    db: Session = Depends(get_db_session),
    _: Usuario | None = Depends(require_permission("products:write")),
) -> ProdutoFornecedorRead:
    if db.get(Produto, product_id) is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    if db.get(Fornecedor, payload.fornecedor_id) is None:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado.")
    if payload.preferencial:
        db.query(ProdutoFornecedor).filter(
            ProdutoFornecedor.produto_id == product_id
        ).update({"preferencial": False}, synchronize_session=False)
    link = ProdutoFornecedor(produto_id=product_id, **payload.model_dump())
    db.add(link)
    try:
        db.commit()
        db.refresh(link)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Este fornecedor já está relacionado ao produto.",
        ) from None
    return ProdutoFornecedorRead.model_validate(link)
