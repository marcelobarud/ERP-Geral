import { request, requestJson } from '../../services/httpClient'
import type { CommercialDocumentPayload, Order, OrderStatus, PaymentCondition, Quote, QuoteStatus, SaleReturn } from './types'

function query(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => { if (value !== undefined && value !== '') search.set(key, String(value)) })
  const encoded = search.toString()
  return encoded ? `?${encoded}` : ''
}

export function listPaymentConditions(includeInactive = false): Promise<PaymentCondition[]> {
  return request<PaymentCondition[]>(`/api/commercial/payment-conditions${includeInactive ? '?include_inactive=true' : ''}`)
}

export function createPaymentCondition(payload: Pick<PaymentCondition, 'codigo' | 'nome' | 'descricao'>): Promise<PaymentCondition> {
  return requestJson<PaymentCondition>('/api/commercial/payment-conditions', 'POST', payload)
}

export function updatePaymentCondition(id: number, payload: Partial<Pick<PaymentCondition, 'codigo' | 'nome' | 'descricao' | 'ativo'>>): Promise<PaymentCondition> {
  return requestJson<PaymentCondition>(`/api/commercial/payment-conditions/${id}`, 'PATCH', payload)
}

export function listQuotes(filters: { search?: string; status?: QuoteStatus } = {}): Promise<Quote[]> {
  return request<Quote[]>(`/api/commercial/quotes${query(filters)}`)
}
export function getQuote(id: number): Promise<Quote> { return request<Quote>(`/api/commercial/quotes/${id}`) }
export function createQuote(payload: CommercialDocumentPayload): Promise<Quote> { return requestJson<Quote>('/api/commercial/quotes', 'POST', payload) }
export function updateQuote(id: number, payload: Partial<CommercialDocumentPayload>): Promise<Quote> { return requestJson<Quote>(`/api/commercial/quotes/${id}`, 'PATCH', payload) }
export function updateQuoteStatus(id: number, status: QuoteStatus): Promise<Quote> { return requestJson<Quote>(`/api/commercial/quotes/${id}/status`, 'PATCH', { status }) }
export function convertQuoteToOrder(id: number): Promise<Order> { return requestJson<Order>(`/api/commercial/quotes/${id}/convert-to-order`, 'POST', {}) }
export function quotePrintUrl(id: number): string { return `/api/commercial/quotes/${id}/print` }

export function listOrders(filters: { search?: string; status?: OrderStatus } = {}): Promise<Order[]> {
  return request<Order[]>(`/api/commercial/orders${query(filters)}`)
}
export function getOrder(id: number): Promise<Order> { return request<Order>(`/api/commercial/orders/${id}`) }
export function createOrder(payload: CommercialDocumentPayload): Promise<Order> { return requestJson<Order>('/api/commercial/orders', 'POST', payload) }
export function updateOrder(id: number, payload: Partial<CommercialDocumentPayload>): Promise<Order> { return requestJson<Order>(`/api/commercial/orders/${id}`, 'PATCH', payload) }
export function updateOrderStatus(id: number, status: OrderStatus): Promise<Order> { return requestJson<Order>(`/api/commercial/orders/${id}/status`, 'PATCH', { status }) }
export function convertOrderToSale(id: number): Promise<unknown> { return requestJson<unknown>(`/api/commercial/orders/${id}/convert-to-sale`, 'POST', {}) }
export function orderPrintUrl(id: number): string { return `/api/commercial/orders/${id}/print` }

export function listReturns(status?: SaleReturn['status']): Promise<SaleReturn[]> { return request<SaleReturn[]>(`/api/sales/returns${status ? `?status=${status}` : ''}`) }
export function createReturn(saleId: number, payload: { motivo: string; itens: { venda_item_id: number; quantidade: string }[] }): Promise<SaleReturn> { return requestJson<SaleReturn>(`/api/sales/${saleId}/returns`, 'POST', payload) }
export function approveReturn(id: number): Promise<SaleReturn> { return requestJson<SaleReturn>(`/api/sales/returns/${id}/approve`, 'POST', {}) }
