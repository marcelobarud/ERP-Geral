// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import * as suppliersApi from './api'
import { SuppliersPage } from './SuppliersPage'

afterEach(() => {
  cleanup()
})

vi.mock('./api', () => ({
  createSupplier: vi.fn(),
  deleteSupplier: vi.fn(),
  getSupplier: vi.fn(),
  listSuppliers: vi.fn(),
  updateSupplier: vi.fn(),
}))

const supplier = {
  id: 1,
  nome: 'Fornecedor de teste',
  cidade: 'São Paulo',
  estado: 'SP',
  rua: 'Rua A',
  numero: '10',
  complemento: null,
  cnpj: '12.345.678/0001-90',
}

describe('SuppliersPage relational details', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(suppliersApi.listSuppliers).mockResolvedValue([supplier])
    vi.mocked(suppliersApi.getSupplier).mockResolvedValue({
      ...supplier,
      produtos: [{ id: 7, nome: 'Produto com nome suficientemente longo para quebrar linha' }],
    })
  })

  it('shows supplied products in the supplier detail', async () => {
    render(<SuppliersPage />)

    await screen.findByText('Fornecedor de teste')
    fireEvent.click(screen.getByRole('button', { name: 'Ver' }))

    expect(await screen.findByText('Produtos fornecidos')).toBeTruthy()
    expect(screen.getByText('Produto com nome suficientemente longo para quebrar linha')).toBeTruthy()
    expect(suppliersApi.getSupplier).toHaveBeenCalledWith(supplier.id)
  })

  it('shows an explicit empty state when the supplier has no products', async () => {
    vi.mocked(suppliersApi.getSupplier).mockResolvedValue({ ...supplier, produtos: [] })
    render(<SuppliersPage />)

    await screen.findByText('Fornecedor de teste')
    fireEvent.click(screen.getByRole('button', { name: 'Ver' }))

    expect(await screen.findByText('Nenhum produto associado a este fornecedor.')).toBeTruthy()
  })

  it('applies and clears the visible supplier filters', async () => {
    render(<SuppliersPage />)

    await screen.findByText('Fornecedor de teste')
    expect(screen.queryByRole('dialog', { name: 'Filtros detalhados' })).toBeNull()
    fireEvent.change(screen.getByRole('searchbox', { name: 'Pesquisar fornecedores' }), { target: { value: 'Fornecedor' } })
    fireEvent.click(screen.getByRole('button', { name: 'Filtros' }))
    expect(screen.getByRole('option', { name: 'São Paulo' })).toBeTruthy()
    expect(screen.getByRole('option', { name: 'SP' })).toBeTruthy()
    fireEvent.change(screen.getByRole('combobox', { name: 'Cidade' }), { target: { value: 'São Paulo' } })
    fireEvent.change(screen.getByRole('combobox', { name: 'Estado' }), { target: { value: 'SP' } })
    fireEvent.click(screen.getByRole('button', { name: 'Aplicar filtros' }))

    await waitFor(() => expect(suppliersApi.listSuppliers).toHaveBeenCalledWith(expect.objectContaining({ search: 'Fornecedor', city: 'São Paulo', state: 'SP', page: 1, pageSize: 20 })))
    fireEvent.click(screen.getByRole('button', { name: /Filtros \(2\)/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Limpar filtros' }))
    await waitFor(() => expect(suppliersApi.listSuppliers).toHaveBeenCalledWith(expect.objectContaining({ page: 1, pageSize: 20 })))
  })

  it('updates the global search after a debounce and restores the full list when cleared', async () => {
    render(<SuppliersPage />)

    await screen.findByText('Fornecedor de teste')
    const search = screen.getByRole('searchbox', { name: 'Pesquisar fornecedores' })
    fireEvent.change(search, { target: { value: 'For' } })
    fireEvent.change(search, { target: { value: 'Fornecedor' } })

    await waitFor(() => expect(suppliersApi.listSuppliers).toHaveBeenCalledWith(expect.objectContaining({ search: 'Fornecedor', page: 1, pageSize: 20 })), { timeout: 1000 })
    expect(suppliersApi.listSuppliers).not.toHaveBeenCalledWith(expect.objectContaining({ search: 'For' }))

    fireEvent.click(screen.getByRole('button', { name: 'Limpar pesquisa' }))
    await waitFor(() => expect(suppliersApi.listSuppliers).toHaveBeenCalledWith(expect.objectContaining({ page: 1, pageSize: 20 })), { timeout: 1000 })
  })
})
