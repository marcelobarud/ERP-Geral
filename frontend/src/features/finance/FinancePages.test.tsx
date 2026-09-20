// @vitest-environment jsdom

import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import * as financeApi from './api'
import { FinancialTitlesPage } from './FinancePages'

vi.mock('./api', () => ({
  listAccounts: vi.fn(),
  listTitles: vi.fn(),
  settleInstallment: vi.fn(),
}))

afterEach(cleanup)

const title = {
  id: 1,
  numero: 'VENDA-19',
  tipo: 'RECEBER' as const,
  cliente_id: 4,
  fornecedor_id: null,
  categoria_id: null,
  origem_tipo: 'VENDA',
  origem_id: 19,
  valor_original: '1219.00',
  valor_liquidado: '0.00',
  saldo: '1219.00',
  status: 'ABERTO' as const,
  descricao: 'Venda #19',
  created_at: '2026-09-19T10:00:00Z',
  updated_at: '2026-09-19T10:00:00Z',
  parcelas: [],
}

describe('FinancialTitlesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(financeApi.listAccounts).mockResolvedValue([])
    vi.mocked(financeApi.listTitles).mockResolvedValue([title])
  })

  it('expõe a hierarquia completa do título para a adaptação mobile', async () => {
    render(<FinancialTitlesPage kind="RECEBER" />)

    expect(await screen.findByText('VENDA-19')).toBeTruthy()
    expect(screen.getByText('Venda #19')).toBeTruthy()
    expect(screen.getAllByText('VENDA #19').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('R$ 1219,00').length).toBe(2)
    expect(screen.getAllByText('Aberto').length).toBe(2)
    expect(screen.getByRole('button', { name: 'Ver parcelas' })).toBeTruthy()

    const row = screen.getByText('VENDA-19').closest('tr')
    expect(row).toBeTruthy()
    expect(row?.querySelector('[data-label="Título"]')).toBeTruthy()
    expect(row?.querySelector('[data-label="Origem"]')).toBeTruthy()
    expect(row?.querySelector('[data-label="Valor"]')).toBeTruthy()
    expect(row?.querySelector('[data-label="Saldo"]')).toBeTruthy()
    expect(row?.querySelector('[data-label="Status"]')).toBeTruthy()
    expect(row?.querySelector('[data-label="Ações"]')).toBeTruthy()
  })
})
