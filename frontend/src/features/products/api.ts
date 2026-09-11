import { request, requestJson } from '../../services/httpClient'
import { attachPagination, type PaginatedItems, type PaginatedResponse } from '../../types/pagination'
import { listSuppliers } from '../suppliers/api'
import type { Supplier } from '../suppliers/types'
import type { Product, ProductPayload } from './types'

export type ProductListFilters = {
  search?: string
  category?: string
  supplierId?: number | ''
  costMin?: string
  costMax?: string
  salePriceMin?: string
  salePriceMax?: string
  page?: number
  pageSize?: number
}

export function listProducts(filters: ProductListFilters = {}): Promise<PaginatedItems<Product>> {
  const params = new URLSearchParams()
  const search = filters.search?.trim()
  const category = filters.category?.trim()
  if (search) params.set('search', search)
  if (category) params.set('category', category)
  if (filters.supplierId) params.set('supplier_id', String(filters.supplierId))
  if (filters.costMin?.trim()) params.set('cost_min', filters.costMin.trim())
  if (filters.costMax?.trim()) params.set('cost_max', filters.costMax.trim())
  if (filters.salePriceMin?.trim()) params.set('sale_price_min', filters.salePriceMin.trim())
  if (filters.salePriceMax?.trim()) params.set('sale_price_max', filters.salePriceMax.trim())
  if (filters.page && filters.page > 1) params.set('page', String(filters.page))
  if (filters.pageSize) params.set('page_size', String(filters.pageSize))
  const query = params.toString()
  return request<PaginatedResponse<Product> | Product[]>(`/api/products${query ? `?${query}` : ''}`).then((body) => Array.isArray(body) ? attachPagination(body, { page: 1, page_size: body.length || 20, total: body.length, total_pages: body.length ? 1 : 0 }) : attachPagination(body.items, { page: body.page, page_size: body.page_size, total: body.total, total_pages: body.total_pages }))
}

export function getProduct(id: number): Promise<Product> {
  return request<Product>(`/api/products/${id}`)
}

export function createProduct(payload: ProductPayload): Promise<Product> {
  return requestJson<Product>('/api/products', 'POST', payload)
}

export function updateProduct(
  id: number,
  payload: Partial<ProductPayload>,
): Promise<Product> {
  return requestJson<Product>(`/api/products/${id}`, 'PATCH', payload)
}

export function deleteProduct(id: number): Promise<void> {
  return request<unknown>(`/api/products/${id}`, { method: 'DELETE' }).then(() => undefined)
}

export function listProductSuppliers(): Promise<Supplier[]> {
  return listSuppliers()
}
