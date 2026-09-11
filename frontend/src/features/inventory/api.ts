import { request, requestJson } from '../../services/httpClient'
import type { Balance, Deposit, Inventory, Movement } from './types'

export function listDeposits(): Promise<Deposit[]> { return request<Deposit[]>('/api/inventory/deposits') }
export function updateDeposit(id: number, payload: Partial<Pick<Deposit, 'codigo' | 'nome' | 'ativo' | 'padrao'>>): Promise<Deposit> { return requestJson<Deposit>(`/api/inventory/deposits/${id}`, 'PATCH', payload) }
export function createDeposit(payload: { codigo: string; nome: string; padrao: boolean }): Promise<Deposit> { return requestJson<Deposit>('/api/inventory/deposits', 'POST', payload) }
export function listBalances(depositId: number): Promise<Balance[]> { return request<Balance[]>(`/api/inventory/balances?deposit_id=${depositId}`) }
export function listMovements(filters: { productId?: number; depositId?: number } = {}): Promise<Movement[]> { const params = new URLSearchParams(); if (filters.productId) params.set('product_id', String(filters.productId)); if (filters.depositId) params.set('deposit_id', String(filters.depositId)); const query = params.toString(); return request<Movement[]>(`/api/inventory/movements${query ? `?${query}` : ''}`) }
export function createMovement(payload: { produto_id: number; deposito_id: number; tipo: string; quantidade: string; data_movimentacao: string; origem: string; observacao: string; chave_idempotencia?: string }): Promise<Movement> { return requestJson<Movement>('/api/inventory/movements', 'POST', payload) }
export function listInventories(): Promise<Inventory[]> { return request<Inventory[]>('/api/inventory/inventories') }
export function createInventory(payload: { deposito_id: number; data_inventario: string; observacao: string; itens: { produto_id: number; quantidade_contada: string }[] }): Promise<Inventory> { return requestJson<Inventory>('/api/inventory/inventories', 'POST', payload) }
export function confirmInventory(id: number): Promise<Inventory> { return requestJson<Inventory>(`/api/inventory/inventories/${id}/confirm`, 'POST', {}) }
