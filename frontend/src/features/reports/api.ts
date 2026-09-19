import { request } from '../../services/httpClient'

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
  balances: Array<{ produto_id: number; quantidade: number; abaixo_do_minimo: boolean }>
  below_minimum: Array<{ produto_id: number; quantidade: number; abaixo_do_minimo: boolean }>
  movement_count: number
}

export type FinanceReport = {
  previsto_receber: number
  previsto_pagar: number
  realizado_receber: number
  realizado_pagar: number
  receivable_titles: number
  payable_titles: number
  overdue_installments: number
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

export function getStockReport(): Promise<StockReport> {
  return request<StockReport>('/api/reports/stock')
}

export function getFinanceReport(): Promise<FinanceReport> {
  return request<FinanceReport>('/api/reports/finance')
}
