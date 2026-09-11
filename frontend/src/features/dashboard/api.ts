import { request } from '../../services/httpClient'

export type DashboardSummary = {
  customers: number
  products: number
  suppliers: number
  employees: number
  sales: number
}

export function getDashboardSummary(): Promise<DashboardSummary> {
  return request<DashboardSummary>('/api/dashboard/summary')
}
