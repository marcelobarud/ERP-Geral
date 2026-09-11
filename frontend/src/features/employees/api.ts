import { request, requestJson } from '../../services/httpClient'
import { attachPagination, type PaginatedItems, type PaginatedResponse } from '../../types/pagination'
import type { Employee, EmployeePayload } from './types'

export type EmployeeListOptions = {
  active?: boolean
  city?: string
  state?: string
  page?: number
  pageSize?: number
}

export function listEmployees(
  activeOnly = false,
  search = '',
  options: EmployeeListOptions = {},
): Promise<PaginatedItems<Employee>> {
  const params = new URLSearchParams()
  const active = options.active ?? (activeOnly ? true : undefined)
  if (active !== undefined) params.set('active', String(active))
  const normalizedSearch = search.trim()
  if (normalizedSearch) params.set('search', normalizedSearch)
  const city = options.city?.trim()
  const state = options.state?.trim()
  if (city) params.set('city', city)
  if (state) params.set('state', state)
  if (options.page && options.page > 1) params.set('page', String(options.page))
  if (options.pageSize) params.set('page_size', String(options.pageSize))
  const query = params.toString()
  return request<PaginatedResponse<Employee> | Employee[]>(`/api/employees${query ? `?${query}` : ''}`).then((body) => Array.isArray(body) ? attachPagination(body, { page: 1, page_size: body.length || 20, total: body.length, total_pages: body.length ? 1 : 0 }) : attachPagination(body.items, { page: body.page, page_size: body.page_size, total: body.total, total_pages: body.total_pages }))
}

export function getEmployee(id: number): Promise<Employee> {
  return request<Employee>(`/api/employees/${id}`)
}

export function createEmployee(payload: EmployeePayload): Promise<Employee> {
  return requestJson<Employee>('/api/employees', 'POST', payload)
}

export function updateEmployee(
  id: number,
  payload: Partial<EmployeePayload>,
): Promise<Employee> {
  return requestJson<Employee>(`/api/employees/${id}`, 'PATCH', payload)
}

export function deleteEmployee(id: number): Promise<void> {
  return request<unknown>(`/api/employees/${id}`, { method: 'DELETE' }).then(() => undefined)
}
