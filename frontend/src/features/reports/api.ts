import { request } from '../../services/httpClient'
import type { DashboardAnalyticsGranularity, DashboardAnalyticsPeriod } from '../dashboard/analytics'

export type ErpDashboard = {
  customers: number
  products: number
  completed_sales: number
  low_stock_products: number
  receivable_open: number
  payable_open: number
  realized_receivable: number
  realized_payable: number
}

export type CommercialReport = {
  sales: number
  completed_sales: number
  cancelled_sales: number
  approved_returns: number
  granularity?: 'day' | 'week' | 'month'
  sales_trend?: Array<{ bucket: string; sales_value: number; completed_sales: number }>
  by_customer: Array<{ customer_id: number | null; customer_name?: string | null; sales: number; total: number }>
  by_product: Array<{ product_id: number; product_name?: string | null; quantity: number; total: number }>
}

export type PurchasesReport = {
  total_orders: number
  pending_receipts: number
  quotes: number
}

export type StockReport = {
  balances: StockReportBalance[]
  below_minimum: StockReportBalance[]
  movement_count: number
  active_products: number
  products_with_balance: number
  period: DashboardAnalyticsPeriod
  date_from: string
  date_to: string
  granularity: DashboardAnalyticsGranularity
  movement_entries: number
  movement_exits: number
  movement_count_in_period: number
  movement_series: Array<{ bucket: string; entries: number; exits: number }>
  deposit: { id: number; code: string; name: string }
}

export type StockReportBalance = {
  produto_id: number
  deposito_id: number
  saldo: string | number
  estoque_minimo: string | number
  abaixo_do_minimo: boolean
  product_name: string
  sku: string
  unit: string
  deficit: string | number
  shortfall_percent: number | null
}

export type FinanceReport = {
  previsto_receber: string | number
  previsto_pagar: string | number
  realizado_receber: string | number
  realizado_pagar: string | number
  receivable_titles: number
  payable_titles: number
  overdue_installments: number
  overdue_open_installments: number
  overdue_receivable: number
  overdue_payable: number
  period: DashboardAnalyticsPeriod
  date_from: string
  date_to: string
  granularity: DashboardAnalyticsGranularity
  commitments: Array<{ bucket: string; receivable: number; payable: number }>
}

function dateQuery(filters: { dateFrom?: string; dateTo?: string } = {}) {
  const params = new URLSearchParams()
  if (filters.dateFrom) params.set('date_from', filters.dateFrom)
  if (filters.dateTo) params.set('date_to', filters.dateTo)
  const query = params.toString()
  return query ? `?${query}` : ''
}

export function getErpDashboard(): Promise<ErpDashboard> {
  return request<ErpDashboard>('/api/reports/dashboard')
}

export function getCommercialReport(filters: { dateFrom?: string; dateTo?: string } = {}): Promise<CommercialReport> {
  return request<CommercialReport>(`/api/reports/commercial${dateQuery(filters)}`)
}

export function getPurchasesReport(): Promise<PurchasesReport> {
  return request<PurchasesReport>('/api/reports/purchases')
}

export function getStockReport(period: DashboardAnalyticsPeriod = '12m'): Promise<StockReport> {
  return request<StockReport>(`/api/reports/stock?period=${period}`)
}

export function getFinanceReport(period: DashboardAnalyticsPeriod = '12m'): Promise<FinanceReport> {
  return request<FinanceReport>(`/api/reports/finance?period=${period}`)
}
