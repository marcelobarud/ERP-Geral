import { request, requestJson } from '../../services/httpClient'
import type { Cashflow, FinancialAccount, FinancialTitle } from './types'

export function listAccounts(): Promise<FinancialAccount[]> { return request<FinancialAccount[]>('/api/finance/accounts') }
export function createAccount(payload: { nome: string; saldo_inicial: string }): Promise<FinancialAccount> { return requestJson<FinancialAccount>('/api/finance/accounts', 'POST', payload) }
export function listTitles(tipo?: 'RECEBER' | 'PAGAR', status?: string): Promise<FinancialTitle[]> { const params = new URLSearchParams(); if (tipo) params.set('tipo', tipo); if (status) params.set('status', status); const query = params.toString(); return request<FinancialTitle[]>(`/api/finance/titles${query ? `?${query}` : ''}`) }
export function settleInstallment(id: number, payload: { conta_id: number; valor: string; data_liquidacao: string; observacao?: string | null }): Promise<unknown> { return requestJson<unknown>(`/api/finance/installments/${id}/settlements`, 'POST', payload) }
export function reverseSettlement(id: number): Promise<unknown> { return requestJson<unknown>(`/api/finance/settlements/${id}/reverse`, 'POST', {}) }
export function getCashflow(): Promise<Cashflow> { return request<Cashflow>('/api/finance/cashflow') }
