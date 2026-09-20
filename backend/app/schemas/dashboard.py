from datetime import date
from typing import Literal

from app.schemas.base import ReadModel


class DashboardSummaryRead(ReadModel):
    customers: int
    products: int
    suppliers: int
    employees: int
    sales: int


DashboardAnalyticsPeriod = Literal["30d", "90d", "6m", "12m"]
DashboardAnalyticsGranularity = Literal["day", "week", "month"]


class DashboardSalesTrendRead(ReadModel):
    bucket: date
    sales_value: float
    completed_sales: int


class DashboardFinanceTrendRead(ReadModel):
    bucket: date
    receivable: float
    payable: float


class DashboardStockAttentionRead(ReadModel):
    product_id: int
    product_name: str
    shortfall_percent: float
    saldo: float
    estoque_minimo: float


class DashboardAnalyticsRead(ReadModel):
    period: DashboardAnalyticsPeriod
    date_from: date
    date_to: date
    granularity: DashboardAnalyticsGranularity
    sales_trend: list[DashboardSalesTrendRead]
    finance_trend: list[DashboardFinanceTrendRead]
    stock_attention: list[DashboardStockAttentionRead]
