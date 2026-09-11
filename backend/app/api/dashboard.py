from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import require_authenticated
from app.db.session import get_db_session
from app.models import Cliente, Fornecedor, Funcionario, Produto, Venda
from app.schemas.dashboard import DashboardSummaryRead

router = APIRouter(
    prefix="/api/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(require_authenticated)],
)


@router.get("/summary", response_model=DashboardSummaryRead)
def get_dashboard_summary(
    db: Session = Depends(get_db_session),
) -> DashboardSummaryRead:
    return DashboardSummaryRead(
        customers=db.scalar(select(func.count()).select_from(Cliente)) or 0,
        products=db.scalar(select(func.count()).select_from(Produto)) or 0,
        suppliers=db.scalar(select(func.count()).select_from(Fornecedor)) or 0,
        employees=db.scalar(select(func.count()).select_from(Funcionario)) or 0,
        sales=db.scalar(select(func.count()).select_from(Venda)) or 0,
    )
