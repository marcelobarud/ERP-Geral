import { request } from '../../services/httpClient'
import type { DashboardAnalytics, DashboardAnalyticsPeriod } from './analytics'

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

export function getDashboardAnalytics(
  period: DashboardAnalyticsPeriod = '12m',
): Promise<DashboardAnalytics> {
  return request<DashboardAnalytics>(`/api/reports/dashboard/analytics?period=${period}`)
}
