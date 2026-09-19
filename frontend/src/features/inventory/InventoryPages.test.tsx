// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import * as productsApi from '../products/api'
import * as inventoryApi from './api'
import { BalancesPage } from './InventoryPages'

afterEach(() => {
  cleanup()
})

vi.mock('./api', () => ({
  listBalances: vi.fn(),
  listDeposits: vi.fn(),
}))

vi.mock('../products/api', () => ({
  listProducts: vi.fn(),
}))

const deposits = [{
  id: 1,
  codigo: 'DEP-01',
  nome: 'Depósito principal',
  ativo: true,
  padrao: true,
  created_at: '',
  updated_at: '',
}]

const products = [
  { id: 1, nome: 'Notebook empresarial', categoria: 'Tecnologia', preco_custo: '10.000', preco_venda: '15.000', fornecedor_id: 1 },
  { id: 2, nome: 'Teclado sem fio', categoria: 'Escritório', preco_custo: '4.000', preco_venda: '8.000', fornecedor_id: 1 },
] as Awaited<ReturnType<typeof productsApi.listProducts>>

const balances = [
  { produto_id: 1, deposito_id: 1, saldo: '2.000', estoque_minimo: '5.000', abaixo_do_minimo: true },
  { produto_id: 2, deposito_id: 1, saldo: '12.000', estoque_minimo: '4.000', abaixo_do_minimo: false },
]

describe('BalancesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(inventoryApi.listDeposits).mockResolvedValue(deposits)
    vi.mocked(inventoryApi.listBalances).mockResolvedValue(balances)
    vi.mocked(productsApi.listProducts).mockResolvedValue(products)
  })

  it('uses the compact semantic boolean filter and filters low stock rows', async () => {
    render(<BalancesPage />)

    expect(await screen.findByRole('cell', { name: 'Notebook empresarial' })).toBeTruthy()
    const lowOnly = screen.getByRole('checkbox', { name: 'Abaixo do mínimo' })
    expect(lowOnly.closest('label')?.classList.contains('filter-checkbox')).toBe(true)
    const table = within(screen.getByRole('table'))
    expect(table.getByText('Teclado sem fio')).toBeTruthy()

    fireEvent.click(lowOnly)

    await waitFor(() => expect(table.queryByText('Teclado sem fio')).toBeNull())
    expect(table.getByText('Notebook empresarial')).toBeTruthy()
  })

  it('keeps the selected deposit query and category filter local to the collection', async () => {
    render(<BalancesPage />)

    await screen.findByRole('cell', { name: 'Notebook empresarial' })
    expect(inventoryApi.listBalances).toHaveBeenCalledWith(1)

    fireEvent.change(screen.getByRole('combobox', { name: 'Categoria' }), { target: { value: 'Tecnologia' } })
    const table = within(screen.getByRole('table'))
    expect(table.getByText('Notebook empresarial')).toBeTruthy()
    expect(table.queryByText('Teclado sem fio')).toBeNull()
  })
})
