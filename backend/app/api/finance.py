from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import require_authenticated, require_permission
from app.db.session import get_db_session
from app.models import CategoriaFinanceira, ContaFinanceira, TituloFinanceiro
from app.schemas.finance import (
    CashflowRead,
    FinancialAccountCreate,
    FinancialAccountRead,
    FinancialCategoryCreate,
    FinancialCategoryRead,
    FinancialSettlementCreate,
    FinancialSettlementRead,
    FinancialTitleCreate,
    FinancialTitleRead,
)
from app.services.finance import (
    FinanceConflict,
    FinanceNotFound,
    cashflow_summary,
    create_title,
    get_title,
    reverse_settlement,
    settle_installment,
    title_query,
    title_to_read,
)

router = APIRouter(
    prefix="/api/finance",
    tags=["finance"],
    dependencies=[Depends(require_authenticated)],
)


@router.get("/categories", response_model=list[FinancialCategoryRead])
def list_categories(db: Session = Depends(get_db_session)):
    return [
        FinancialCategoryRead.model_validate(item)
        for item in db.scalars(
            select(CategoriaFinanceira).order_by(CategoriaFinanceira.nome)
        ).all()
    ]


@router.post(
    "/categories",
    response_model=FinancialCategoryRead,
    status_code=201,
    dependencies=[Depends(require_permission("finance:write"))],
)
def create_category(
    payload: FinancialCategoryCreate, db: Session = Depends(get_db_session)
):
    item = CategoriaFinanceira(**payload.model_dump())
    db.add(item)
    try:
        db.commit()
        db.refresh(item)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Categoria já cadastrada."
        ) from None
    return FinancialCategoryRead.model_validate(item)


@router.get("/accounts", response_model=list[FinancialAccountRead])
def list_accounts(db: Session = Depends(get_db_session)):
    return [
        FinancialAccountRead.model_validate(item)
        for item in db.scalars(
            select(ContaFinanceira).where(ContaFinanceira.ativo.is_(True))
        ).all()
    ]


@router.post(
    "/accounts",
    response_model=FinancialAccountRead,
    status_code=201,
    dependencies=[Depends(require_permission("finance:write"))],
)
def create_account(
    payload: FinancialAccountCreate, db: Session = Depends(get_db_session)
):
    account = ContaFinanceira(**payload.model_dump())
    db.add(account)
    try:
        db.commit()
        db.refresh(account)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Conta já cadastrada.") from None
    return FinancialAccountRead.model_validate(account)


def create_title_endpoint(title_type: str, payload: FinancialTitleCreate, db: Session):
    try:
        return title_to_read(create_title(db, title_type, payload))
    except FinanceNotFound as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from None
    except FinanceConflict as exception:
        raise HTTPException(status_code=409, detail=str(exception)) from None


@router.post(
    "/receivables",
    response_model=FinancialTitleRead,
    status_code=201,
    dependencies=[Depends(require_permission("finance:write"))],
)
def create_receivable(
    payload: FinancialTitleCreate, db: Session = Depends(get_db_session)
):
    return create_title_endpoint("RECEBER", payload, db)


@router.post(
    "/payables",
    response_model=FinancialTitleRead,
    status_code=201,
    dependencies=[Depends(require_permission("finance:write"))],
)
def create_payable(
    payload: FinancialTitleCreate, db: Session = Depends(get_db_session)
):
    return create_title_endpoint("PAGAR", payload, db)


@router.get("/titles", response_model=list[FinancialTitleRead])
def list_titles(
    title_type: str | None = Query(default=None, alias="tipo"),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db_session),
):
    query = title_query().order_by(TituloFinanceiro.created_at.desc())
    if title_type:
        query = query.where(TituloFinanceiro.tipo == title_type)
    titles = [title_to_read(item) for item in db.scalars(query).all()]
    if status_filter:
        titles = [item for item in titles if item.status == status_filter]
    return titles


@router.get("/titles/{title_id}", response_model=FinancialTitleRead)
def get_title_endpoint(title_id: int, db: Session = Depends(get_db_session)):
    title = get_title(db, title_id)
    if title is None:
        raise HTTPException(status_code=404, detail="Título não encontrado.")
    return title_to_read(title)


@router.post(
    "/installments/{installment_id}/settlements",
    response_model=FinancialSettlementRead,
    status_code=201,
    dependencies=[Depends(require_permission("finance:write"))],
)
def settle_endpoint(
    installment_id: int,
    payload: FinancialSettlementCreate,
    db: Session = Depends(get_db_session),
):
    try:
        return FinancialSettlementRead.model_validate(
            settle_installment(
                db,
                installment_id,
                payload.conta_id,
                payload.valor,
                payload.data_liquidacao,
                payload.observacao,
            )
        )
    except FinanceNotFound as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from None
    except FinanceConflict as exception:
        raise HTTPException(status_code=409, detail=str(exception)) from None


@router.post(
    "/settlements/{settlement_id}/reverse",
    response_model=FinancialSettlementRead,
    dependencies=[Depends(require_permission("finance:write"))],
)
def reverse_endpoint(settlement_id: int, db: Session = Depends(get_db_session)):
    try:
        return FinancialSettlementRead.model_validate(
            reverse_settlement(db, settlement_id)
        )
    except FinanceNotFound as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from None


@router.get("/cashflow", response_model=CashflowRead)
def cashflow_endpoint(db: Session = Depends(get_db_session)):
    return cashflow_summary(db)
