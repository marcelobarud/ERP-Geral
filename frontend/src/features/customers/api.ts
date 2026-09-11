import { request, requestJson } from '../../services/httpClient'
import { attachPagination, type PaginatedItems, type PaginatedResponse } from '../../types/pagination'
import type { Customer, CustomerDetails, CustomerPayload } from './types'

export type CustomerListFilters = {
  search?: string
  city?: string
  state?: string
  page?: number
  pageSize?: number
}

export function listCustomers(filters: CustomerListFilters = {}): Promise<PaginatedItems<Customer>> {
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
  return request<PaginatedResponse<Customer> | Customer[]>(`/api/customers${query ? `?${query}` : ''}`).then((body) => Array.isArray(body) ? attachPagination(body, { page: 1, page_size: body.length || 20, total: body.length, total_pages: body.length ? 1 : 0 }) : attachPagination(body.items, { page: body.page, page_size: body.page_size, total: body.total, total_pages: body.total_pages }))
}

export function getCustomer(id: number): Promise<CustomerDetails> {
  return request<CustomerDetails>(`/api/customers/${id}`)
}

export function createCustomer(payload: CustomerPayload): Promise<Customer> {
  return requestJson<Customer>('/api/customers', 'POST', payload)
}

export function updateCustomer(
  id: number,
  payload: Partial<CustomerPayload>,
): Promise<Customer> {
  return requestJson<Customer>(`/api/customers/${id}`, 'PATCH', payload)
}

export function deleteCustomer(id: number): Promise<void> {
  return request<unknown>(`/api/customers/${id}`, { method: 'DELETE' }).then(() => undefined)
}
