// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../services/httpClient'
import * as customersApi from '../customers/api'
import * as employeesApi from '../employees/api'
import * as productsApi from '../products/api'
import * as salesApi from './api'
import { NewSalePage } from './SalesPages'

vi.mock('../customers/api', () => ({ listCustomers: vi.fn() }))
vi.mock('../employees/api', () => ({ listEmployees: vi.fn() }))
vi.mock('../products/api', () => ({ listProducts: vi.fn() }))
vi.mock('./api', () => ({ createSale: vi.fn() }))

const customer = {
  id: 10,
  nome: 'Cliente Teste',
  cidade: 'São Paulo',
  estado: 'SP',
  rua: 'Rua A',
  numero: '10',
  complemento: null,
}

const employee = {
  id: 20,
  nome_completo: 'Funcionário Teste',
  cidade: 'São Paulo',
  estado: 'SP',
  rua: 'Rua B',
  numero: '20',
  complemento: null,
  cpf: '12345678901',
  rg: null,
  data_nascimento: '1990-01-01',
  ativo: true,
}

const inactiveEmployee = { ...employee, id: 21, nome_completo: 'Funcionário Inativo', ativo: false }

const products = [
  { id: 30, nome: 'Produto A', categoria: 'Categoria', preco_custo: '5.00', preco_venda: '10.00', fornecedor_id: 1 },
  { id: 31, nome: 'Produto B', categoria: 'Categoria', preco_custo: '8.00', preco_venda: '20.00', fornecedor_id: 1 },
]

const savedSale = {
  id: 99,
  data_venda: '2026-08-19T13:00:00Z',
  cliente: { id: customer.id, nome: customer.nome },
  funcionario: { id: employee.id, nome_completo: employee.nome_completo },
  itens: [],
  total: '50.00',
}

describe('NewSalePage', () => {
  afterEach(() => cleanup())

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(customersApi.listCustomers).mockResolvedValue([customer])
    vi.mocked(employeesApi.listEmployees).mockResolvedValue([employee])
    vi.mocked(productsApi.listProducts).mockResolvedValue(products)
    vi.mocked(salesApi.createSale).mockResolvedValue(savedSale)
  })

  async function renderReadyPage() {
    render(<NewSalePage />)
    await screen.findByLabelText('Cliente')
    fireEvent.change(screen.getByLabelText('Cliente'), { target: { value: String(customer.id) } })
    fireEvent.change(screen.getByLabelText('Funcionário'), { target: { value: String(employee.id) } })
    fireEvent.change(screen.getByLabelText('Data da venda'), { target: { value: '2026-08-19T10:00' } })
  }

  it('loads dependencies, supports two products and sends only IDs and quantities', async () => {
    await renderReadyPage()
    fireEvent.click(screen.getByRole('button', { name: '+ Adicionar produto' }))
    fireEvent.change(screen.getByLabelText('Produto do item 1'), { target: { value: '30' } })
    fireEvent.change(screen.getByLabelText('Quantidade', { selector: '#sale-quantity-1' }), { target: { value: '2' } })
    fireEvent.click(screen.getByRole('button', { name: '+ Adicionar produto' }))
    fireEvent.change(screen.getByLabelText('Produto do item 2'), { target: { value: '31' } })
    fireEvent.change(screen.getByLabelText('Quantidade', { selector: '#sale-quantity-2' }), { target: { value: '1.500' } })
    expect(screen.getAllByText('R$ 20,00').length).toBeGreaterThanOrEqual(2)
    expect(screen.getByText('R$ 30,00')).toBeTruthy()
    expect(screen.getByText('R$ 50,00')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Salvar venda' }))

    await waitFor(() => expect(salesApi.createSale).toHaveBeenCalledOnce())
    const payload = vi.mocked(salesApi.createSale).mock.calls[0][0]
    expect(payload).toEqual({
      cliente_id: 10,
      funcionario_id: 20,
      data_venda: '2026-08-19T13:00:00.000Z',
      itens: [
        { produto_id: 30, quantidade: '2' },
        { produto_id: 31, quantidade: '1.500' },
      ],
    })
    expect(payload.itens[0]).not.toHaveProperty('preco_unitario')
    expect(payload.itens[0]).not.toHaveProperty('subtotal')
    expect(payload).not.toHaveProperty('total')
    expect(screen.getByText('Venda #99 criada com sucesso. Total confirmado: R$ 50,00.')).toBeTruthy()
  })

  it('requests only active employees for a new sale', async () => {
    vi.mocked(employeesApi.listEmployees).mockImplementation(async (activeOnly = false) => activeOnly ? [employee] : [employee, inactiveEmployee])
    render(<NewSalePage />)
    await screen.findByLabelText('Funcionário')

    expect(employeesApi.listEmployees).toHaveBeenCalledWith(true, '', { page: 1, pageSize: 100 })
    expect(screen.getByRole('option', { name: employee.nome_completo })).toBeTruthy()
    expect(screen.queryByRole('option', { name: inactiveEmployee.nome_completo })).toBeNull()
  })

  it('keeps the add action inside the empty state and shares item guidance', async () => {
    await renderReadyPage()

    const emptyState = screen.getByText('Adicione o primeiro produto').closest('.sale-items-empty')
    expect(emptyState).not.toBeNull()
    expect(within(emptyState as HTMLElement).getByRole('button', { name: '+ Adicionar produto' })).toBeTruthy()

    fireEvent.click(within(emptyState as HTMLElement).getByRole('button', { name: '+ Adicionar produto' }))
    expect(screen.queryByText('Adicione o primeiro produto')).toBeNull()
    expect(screen.getAllByText(/A quantidade aceita até três casas decimais/)).toHaveLength(1)
    expect(screen.getByLabelText('Quantidade', { selector: '#sale-quantity-1' }).getAttribute('aria-describedby')).toBe('sale-items-help')
  })

  it('prevents duplicate products in item selectors', async () => {
    await renderReadyPage()
    fireEvent.click(screen.getByRole('button', { name: '+ Adicionar produto' }))
    fireEvent.change(screen.getByLabelText('Produto do item 1'), { target: { value: '30' } })
    fireEvent.click(screen.getByRole('button', { name: '+ Adicionar produto' }))

    const secondSelector = screen.getByLabelText('Produto do item 2')
    expect(within(secondSelector).queryByRole('option', { name: /Produto A/ })).toBeNull()
  })

  it('rejects invalid quantities before calling the API', async () => {
    await renderReadyPage()
    fireEvent.click(screen.getByRole('button', { name: '+ Adicionar produto' }))
    fireEvent.change(screen.getByLabelText('Produto do item 1'), { target: { value: '30' } })
    fireEvent.change(screen.getByLabelText('Quantidade', { selector: '#sale-quantity-1' }), { target: { value: '0' } })
    fireEvent.click(screen.getByRole('button', { name: 'Salvar venda' }))

    expect(await screen.findByText('Informe quantidades maiores que zero com até três casas decimais.')).toBeTruthy()
    expect(salesApi.createSale).not.toHaveBeenCalled()
  })

  it('keeps the filled form after a 422 response', async () => {
    vi.mocked(salesApi.createSale).mockRejectedValue(new ApiError(422, 'Quantidade inválida.'))
    await renderReadyPage()
    fireEvent.click(screen.getByRole('button', { name: '+ Adicionar produto' }))
    fireEvent.change(screen.getByLabelText('Produto do item 1'), { target: { value: '30' } })
    fireEvent.change(screen.getByLabelText('Quantidade', { selector: '#sale-quantity-1' }), { target: { value: '1.250' } })
    fireEvent.click(screen.getByRole('button', { name: 'Salvar venda' }))

    expect(await screen.findByText('Quantidade inválida.')).toBeTruthy()
    expect(screen.getByLabelText('Cliente')).toHaveProperty('value', String(customer.id))
    expect(screen.getByLabelText('Funcionário')).toHaveProperty('value', String(employee.id))
    expect(screen.getByLabelText('Produto do item 1')).toHaveProperty('value', '30')
    expect(screen.getByLabelText('Quantidade', { selector: '#sale-quantity-1' })).toHaveProperty('value', '1.250')
  })
})
