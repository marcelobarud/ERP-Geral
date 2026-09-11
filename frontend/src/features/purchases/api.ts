import { request, requestJson } from '../../services/httpClient'
import type { Purchase, PurchasePayload, Receipt } from './types'

function listQuery(search?: string, status?: string): string {
  const params = new URLSearchParams()
  if (search?.trim()) params.set('search', search.trim())
  if (status) params.set('status', status)
  const value = params.toString()
  return value ? `?${value}` : ''
}

export function listPurchases(filters: { search?: string; status?: string } = {}): Promise<Purchase[]> { return request<Purchase[]>(`/api/purchases${listQuery(filters.search, filters.status)}`) }
export function getPurchase(id: number): Promise<Purchase> { return request<Purchase>(`/api/purchases/${id}`) }
export function createPurchase(payload: PurchasePayload): Promise<Purchase> { return requestJson<Purchase>('/api/purchases', 'POST', payload) }
export function updatePurchase(id: number, payload: Partial<PurchasePayload>): Promise<Purchase> { return requestJson<Purchase>(`/api/purchases/${id}`, 'PATCH', payload) }
export function updatePurchaseStatus(id: number, status: Purchase['status']): Promise<Purchase> { return requestJson<Purchase>(`/api/purchases/${id}/status`, 'PATCH', { status }) }
export function listReceipts(purchaseId: number): Promise<Receipt[]> { return request<Receipt[]>(`/api/purchases/${purchaseId}/receipts`) }
export function createReceipt(purchaseId: number, payload: { data_recebimento: string; observacao?: string | null; itens: { pedido_item_id: number; quantidade: string; custo_efetivo: string }[] }): Promise<Receipt> { return requestJson<Receipt>(`/api/purchases/${purchaseId}/receipts`, 'POST', payload) }
export function confirmReceipt(id: number): Promise<Receipt> { return requestJson<Receipt>(`/api/purchases/receipts/${id}/confirm`, 'POST', {}) }
