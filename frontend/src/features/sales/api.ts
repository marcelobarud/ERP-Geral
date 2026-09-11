import { request, requestJson } from '../../services/httpClient'
import { attachPagination, type PaginatedItems, type PaginatedResponse } from '../../types/pagination'
import type { Sale, SaleCreatePayload } from './types'

export type SaleListFilters = {
  search?: string
  productId?: number | ''
  customerId?: number | ''
  employeeId?: number | ''
  dateFrom?: string
  dateTo?: string
  totalMin?: string
  totalMax?: string
  status?: 'CONCLUIDA' | 'CANCELADA'
  page?: number
  pageSize?: number
}

export function listSales(filters: SaleListFilters = {}): Promise<PaginatedItems<Sale>> {
  const params = new URLSearchParams()
  const search = filters.search?.trim()
  if (search) params.set('search', search)
  if (filters.productId) params.set('product_id', String(filters.productId))
  if (filters.customerId) params.set('customer_id', String(filters.customerId))
  if (filters.employeeId) params.set('employee_id', String(filters.employeeId))
  if (filters.dateFrom) params.set('date_from', filters.dateFrom)
  if (filters.dateTo) params.set('date_to', filters.dateTo)
  if (filters.totalMin?.trim()) params.set('total_min', filters.totalMin.trim())
  if (filters.totalMax?.trim()) params.set('total_max', filters.totalMax.trim())
  if (filters.status) params.set('status', filters.status)
  if (filters.page && filters.page > 1) params.set('page', String(filters.page))
  if (filters.pageSize) params.set('page_size', String(filters.pageSize))
  const query = params.toString()
  return request<PaginatedResponse<Sale> | Sale[]>(`/api/sales${query ? `?${query}` : ''}`).then((body) => Array.isArray(body) ? attachPagination(body, { page: 1, page_size: body.length || 20, total: body.length, total_pages: body.length ? 1 : 0 }) : attachPagination(body.items, { page: body.page, page_size: body.page_size, total: body.total, total_pages: body.total_pages }))
}

export function getSale(id: number): Promise<Sale> {
  return request<Sale>(`/api/sales/${id}`)
}

export function cancelSale(id: number, motivo?: string): Promise<Sale> {
  return requestJson<Sale>(`/api/sales/${id}/cancel`, 'POST', { motivo: motivo || null })
}

export function createSale(payload: SaleCreatePayload): Promise<Sale> {
  return requestJson<Sale>('/api/sales', 'POST', payload)
}
