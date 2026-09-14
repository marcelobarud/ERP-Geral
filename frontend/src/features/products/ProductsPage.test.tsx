// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import * as productsApi from './api'
import { ProductsPage } from './ProductsPage'

vi.mock('./api', () => ({
  createProduct: vi.fn(),
  deleteProduct: vi.fn(),
  listProductSuppliers: vi.fn(),
  listProducts: vi.fn(),
  updateProduct: vi.fn(),
}))

const supplier = {
  id: 2,
  nome: 'Fornecedor A',
  cidade: 'Campinas',
  estado: 'SP',
  rua: 'Rua B',
  numero: '20',
  complemento: null,
  cnpj: '12.345.678/0001-90',
}

const product = {
  id: 4,
  nome: 'Produto A',
  categoria: 'Categoria A',
  preco_custo: '10.50',
  preco_venda: '18.90',
  fornecedor_id: supplier.id,
}

describe('ProductsPage filters', () => {
  afterEach(() => cleanup())

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(productsApi.listProducts).mockResolvedValue([product])
    vi.mocked(productsApi.listProductSuppliers).mockResolvedValue([supplier])
  })

  it('applies the supplier and decimal range filters and clears them', async () => {
    render(<ProductsPage />)
    await screen.findByText('Produto A')

    fireEvent.change(screen.getByRole('searchbox', { name: 'Pesquisar produtos' }), { target: { value: 'Produto' } })
    expect(screen.queryByRole('dialog', { name: 'Filtros detalhados' })).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Filtros' }))
    expect(screen.getByRole('option', { name: 'Categoria A' })).toBeTruthy()
    expect(screen.getByRole('option', { name: 'Fornecedor A' })).toBeTruthy()
    fireEvent.change(screen.getByRole('combobox', { name: 'Categoria' }), { target: { value: 'Categoria A' } })
    fireEvent.change(screen.getByRole('combobox', { name: 'Fornecedor' }), { target: { value: '2' } })
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Custo mínimo' }), { target: { value: '10.50' } })
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Venda máxima' }), { target: { value: '20.00' } })
    fireEvent.click(screen.getByRole('button', { name: 'Aplicar filtros' }))

    await waitFor(() => expect(productsApi.listProducts).toHaveBeenCalledWith(expect.objectContaining({ search: 'Produto', category: 'Categoria A', supplierId: 2, costMin: '10.50', costMax: '', salePriceMin: '', salePriceMax: '20.00', page: 1, pageSize: 20 })))
    expect(screen.getByText('Filtros ativos')).toBeTruthy()
    expect(screen.getByRole('button', { name: /Busca: Produto/ })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: /Filtros \(5\)/ }))
    fireEvent.click(screen.getAllByRole('button', { name: 'Limpar filtros' })[0])
    await waitFor(() => expect(productsApi.listProducts).toHaveBeenCalledWith(expect.objectContaining({ page: 1, pageSize: 20 })))
  })
})
