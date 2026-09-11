import { request, requestJson } from '../../services/httpClient'
import { attachPagination, type PaginatedItems, type PaginatedResponse } from '../../types/pagination'
import type { Supplier, SupplierDetails, SupplierPayload } from './types'

export type SupplierListFilters = {
  search?: string
  city?: string
  state?: string
  page?: number
  pageSize?: number
}

export function listSuppliers(filters: SupplierListFilters = {}): Promise<PaginatedItems<Supplier>> {
  const params = new URLSearchParams()
  const search = filters.search?.trim()
  const city = filters.city?.trim()
  const state = filters.state?.trim()
  if (search) params.set('search', search)
  if (city) params.set('city', city)
  if (state) params.set('state', state)
  if (filters.page && filters.page > 1) params.set('page', String(filters.page))
  if (filters.pageSize) params.set('page_size', String(filters.pageSize))
  const query = params.toString()
  return request<PaginatedResponse<Supplier> | Supplier[]>(`/api/suppliers${query ? `?${query}` : ''}`).then((body) => Array.isArray(body) ? attachPagination(body, { page: 1, page_size: body.length || 20, total: body.length, total_pages: body.length ? 1 : 0 }) : attachPagination(body.items, { page: body.page, page_size: body.page_size, total: body.total, total_pages: body.total_pages }))
}

export function getSupplier(id: number): Promise<SupplierDetails> {
  return request<SupplierDetails>(`/api/suppliers/${id}`)
}

export function createSupplier(payload: SupplierPayload): Promise<Supplier> {
  return requestJson<Supplier>('/api/suppliers', 'POST', payload)
}

export function updateSupplier(
  id: number,
  payload: Partial<SupplierPayload>,
): Promise<Supplier> {
  return requestJson<Supplier>(`/api/suppliers/${id}`, 'PATCH', payload)
}

export function deleteSupplier(id: number): Promise<void> {
  return request<unknown>(`/api/suppliers/${id}`, { method: 'DELETE' }).then(() => undefined)
}
