from app.schemas.base import ReadModel


class DashboardSummaryRead(ReadModel):
    customers: int
    products: int
    suppliers: int
    employees: int
    sales: int
