// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../services/httpClient'
import * as customersApi from '../customers/api'
import * as employeesApi from '../employees/api'
import * as productsApi from '../products/api'
import * as salesApi from './api'
import { SalesPage } from './SalesPages'

vi.mock('./api', () => ({ listSales: vi.fn(), getSale: vi.fn(), cancelSale: vi.fn() }))
vi.mock('../customers/api', () => ({ listCustomers: vi.fn() }))
vi.mock('../employees/api', () => ({ listEmployees: vi.fn() }))
vi.mock('../products/api', () => ({ listProducts: vi.fn() }))

const sale = {
  id: 70,
  data_venda: '2026-08-19T13:00:00Z',
  cliente: { id: 10, nome: 'Cliente Histórico' },
  funcionario: { id: 20, nome_completo: 'Funcionário Histórico' },
  itens: [{
    id: 700,
    produto: { id: 30, nome: 'Produto Histórico' },
    fornecedor_id: 40,
    fornecedor: { id: 40, nome: 'Fornecedor Histórico' },
    quantidade: '1.500',
    preco_unitario: '12.34',
    subtotal: '18.51',
  }],
  total: '18.51',
}

describe('SalesPage', () => {
  afterEach(() => cleanup())

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(salesApi.listSales).mockResolvedValue([sale])
    vi.mocked(salesApi.getSale).mockResolvedValue(sale)
    vi.mocked(salesApi.cancelSale).mockResolvedValue({ ...sale, status: 'CANCELADA', cancelada_em: '2026-08-19T14:00:00Z', motivo_cancelamento: null })
    vi.mocked(customersApi.listCustomers).mockResolvedValue([{ id: 10, nome: 'Cliente Histórico', cidade: 'São Paulo', estado: 'SP', rua: 'Rua A', numero: '1', complemento: null }])
    vi.mocked(employeesApi.listEmployees).mockResolvedValue([{ id: 20, nome_completo: 'Funcionário Histórico', cidade: 'São Paulo', estado: 'SP', rua: 'Rua B', numero: '2', complemento: null, cpf: '123.456.789-09', rg: null, data_nascimento: '1990-01-01', ativo: false }])
    vi.mocked(productsApi.listProducts).mockResolvedValue([{ id: 30, nome: 'Produto Histórico', categoria: 'Geral', preco_custo: '10.00', preco_venda: '12.34', fornecedor_id: 40 }])
  })

  it('renders the list and shows historical prices and totals in details', async () => {
    render(<SalesPage />)
    await screen.findByText('#70')
    expect(screen.getAllByText('Produto Histórico').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Cliente Histórico').length).toBeGreaterThan(0)
    expect(screen.getByText('R$ 18,51')).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'Ver detalhes' }))
    await waitFor(() => expect(salesApi.getSale).toHaveBeenCalledWith(70))
    expect(await screen.findByRole('dialog', { name: 'Detalhes da venda #70' })).toBeTruthy()
    expect(screen.getAllByText('Produto Histórico').length).toBeGreaterThanOrEqual(2)
    expect(screen.getByText('1,500')).toBeTruthy()
    expect(screen.getByText('Fornecedor Histórico')).toBeTruthy()
    expect(screen.getByText('R$ 12,34')).toBeTruthy()
    expect(screen.getAllByText('R$ 18,51').length).toBeGreaterThanOrEqual(2)
  })

  it.each([
    [2, '2 produtos'],
    [3, '3 produtos'],
  ])('summarizes a sale with %i products in the list', async (itemCount, label) => {
    const multipleItemSale = {
      ...sale,
      itens: Array.from({ length: itemCount }, (_, index) => ({
        ...sale.itens[0],
        id: sale.itens[0].id + index,
        produto: { id: 30 + index, nome: `Produto ${index + 1}` },
      })),
    }
    vi.mocked(salesApi.listSales).mockResolvedValue([multipleItemSale])

    render(<SalesPage />)

    expect(await screen.findByText(label)).toBeTruthy()
  })

  it('renders the empty state', async () => {
    vi.mocked(salesApi.listSales).mockResolvedValue([])
    render(<SalesPage />)

    expect(await screen.findByText('Nenhuma venda registrada ainda')).toBeTruthy()
    expect(screen.getByRole('link', { name: 'Criar nova venda' })).toBeTruthy()
  })

  it('renders an API error state', async () => {
    vi.mocked(salesApi.listSales).mockRejectedValue(new ApiError(500, 'Falha ao consultar vendas.'))
    render(<SalesPage />)

    expect(await screen.findByText('Falha ao consultar vendas.')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Tentar novamente' })).toBeTruthy()
  })

  it('applies the combined historical filters and clears them', async () => {
    render(<SalesPage />)
    await screen.findByText('#70')

    fireEvent.change(screen.getByRole('searchbox', { name: 'Pesquisar vendas' }), { target: { value: '  Produto  ' } })
    expect(screen.queryByRole('dialog', { name: 'Filtros detalhados' })).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Filtros' }))
    expect(screen.getByRole('option', { name: 'Produto Histórico' })).toBeTruthy()
    expect(screen.getByRole('option', { name: 'Cliente Histórico' })).toBeTruthy()
    expect(screen.getByRole('option', { name: 'Funcionário Histórico' })).toBeTruthy()
    fireEvent.change(screen.getByRole('combobox', { name: 'Produto' }), { target: { value: '30' } })
    fireEvent.change(screen.getByRole('combobox', { name: 'Cliente' }), { target: { value: '10' } })
    fireEvent.change(screen.getByRole('combobox', { name: 'Funcionário' }), { target: { value: '20' } })
    fireEvent.change(screen.getByLabelText('Data inicial'), { target: { value: '2026-08-20' } })
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Total mínimo' }), { target: { value: '10.00' } })
    fireEvent.click(screen.getByRole('button', { name: 'Aplicar filtros' }))

    await waitFor(() => expect(salesApi.listSales).toHaveBeenLastCalledWith(expect.objectContaining({ search: 'Produto', productId: 30, customerId: 10, employeeId: 20, dateFrom: '2026-08-20', dateTo: '', totalMin: '10.00', totalMax: '' })))
    fireEvent.click(screen.getByRole('button', { name: /Filtros \(5\)/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Limpar filtros' }))
    await waitFor(() => expect(salesApi.listSales).toHaveBeenLastCalledWith(expect.objectContaining({})))
  })

  it('opens and cancels the explicit sale cancellation confirmation', async () => {
    render(<SalesPage />)
    await screen.findByText('#70')

    fireEvent.click(screen.getByRole('button', { name: 'Cancelar venda' }))

    const dialog = await screen.findByRole('dialog', { name: 'Cancelar venda #70?' })
    expect(within(dialog).getByText(/serão preservados no histórico/)).toBeTruthy()
    fireEvent.click(within(dialog).getByRole('button', { name: 'Voltar' }))

    expect(screen.queryByRole('dialog', { name: 'Cancelar venda #70?' })).toBeNull()
    expect(screen.getByText('#70')).toBeTruthy()
    expect(salesApi.cancelSale).not.toHaveBeenCalled()
  })

  it('cancels the sale after confirmation and preserves it in the list', async () => {
    render(<SalesPage />)
    await screen.findByText('#70')
    fireEvent.click(screen.getByRole('button', { name: 'Cancelar venda' }))
    const dialog = await screen.findByRole('dialog', { name: 'Cancelar venda #70?' })

    fireEvent.click(within(dialog).getByRole('button', { name: 'Cancelar venda' }))

    await waitFor(() => expect(salesApi.cancelSale).toHaveBeenCalledWith(70, undefined))
    expect(screen.getByText('#70')).toBeTruthy()
    expect(await screen.findByText('Venda #70 cancelada com sucesso.')).toBeTruthy()
  })

  it('keeps the sale visible when the cancellation request fails', async () => {
    vi.mocked(salesApi.cancelSale).mockRejectedValue(new ApiError(500, 'Falha ao cancelar venda.'))
    render(<SalesPage />)
    await screen.findByText('#70')
    fireEvent.click(screen.getByRole('button', { name: 'Cancelar venda' }))
    const dialog = await screen.findByRole('dialog', { name: 'Cancelar venda #70?' })

    fireEvent.click(within(dialog).getByRole('button', { name: 'Cancelar venda' }))

    expect(await screen.findByText('Falha ao cancelar venda.')).toBeTruthy()
    expect(screen.getByText('#70')).toBeTruthy()
    expect(screen.queryByText('Venda #70 cancelada com sucesso.')).toBeNull()
  })
})
