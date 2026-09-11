// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import * as customerApi from './customers/api'
import { CustomersPage } from './customers/CustomersPage'
import * as employeeApi from './employees/api'
import { EmployeesPage } from './employees/EmployeesPage'
import * as productApi from './products/api'
import { ProductsPage } from './products/ProductsPage'
import * as supplierApi from './suppliers/api'
import { SuppliersPage } from './suppliers/SuppliersPage'

vi.mock('./customers/api', () => ({
  createCustomer: vi.fn(),
  deleteCustomer: vi.fn(),
  getCustomer: vi.fn(),
  listCustomers: vi.fn(),
  updateCustomer: vi.fn(),
}))
vi.mock('./suppliers/api', () => ({
  createSupplier: vi.fn(),
  deleteSupplier: vi.fn(),
  getSupplier: vi.fn(),
  listSuppliers: vi.fn(),
  updateSupplier: vi.fn(),
}))
vi.mock('./employees/api', () => ({
  createEmployee: vi.fn(),
  deleteEmployee: vi.fn(),
  listEmployees: vi.fn(),
  updateEmployee: vi.fn(),
}))
vi.mock('./products/api', () => ({
  createProduct: vi.fn(),
  deleteProduct: vi.fn(),
  listProducts: vi.fn(),
  listProductSuppliers: vi.fn(),
  updateProduct: vi.fn(),
}))

const customer = {
  id: 1,
  nome: 'Ana Silva',
  cidade: 'São Paulo',
  estado: 'SP',
  rua: 'Rua A',
  numero: '10',
  complemento: null,
}

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

const secondSupplier = { ...supplier, id: 3, nome: 'Fornecedor B', cnpj: '98.765.432/0001-10' }

const employee = {
  id: 4,
  nome_completo: 'Carlos Souza',
  cidade: 'Santos',
  estado: 'SP',
  rua: 'Rua C',
  numero: '30',
  complemento: null,
  cpf: '123.456.789-00',
  rg: null,
  data_nascimento: '1990-01-01',
  ativo: true,
}

const product = {
  id: 5,
  nome: 'Produto A',
  categoria: 'Categoria A',
  preco_custo: '10.50',
  preco_venda: '18.90',
  fornecedor_id: supplier.id,
}

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

beforeEach(() => {
  vi.mocked(customerApi.listCustomers).mockResolvedValue([customer])
  vi.mocked(customerApi.updateCustomer).mockResolvedValue({ ...customer, nome: 'Ana Atualizada' })
  vi.mocked(supplierApi.listSuppliers).mockResolvedValue([supplier])
  vi.mocked(supplierApi.updateSupplier).mockResolvedValue({ ...supplier, nome: 'Fornecedor Atualizado' })
  vi.mocked(employeeApi.listEmployees).mockResolvedValue([employee])
  vi.mocked(employeeApi.updateEmployee).mockResolvedValue(employee)
  vi.mocked(productApi.listProducts).mockResolvedValue([product])
  vi.mocked(productApi.listProductSuppliers).mockResolvedValue([supplier, secondSupplier])
  vi.mocked(productApi.updateProduct).mockResolvedValue({ ...product, preco_venda: '19.00', fornecedor_id: secondSupplier.id })
})

describe('edição dos cadastros', () => {
  it('edita cliente sem enviar o id e atualiza a listagem', async () => {
    render(<CustomersPage />)
    await screen.findByText('Ana Silva')
    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
    fireEvent.change(screen.getByLabelText('Nome'), { target: { value: 'Ana Atualizada' } })
    fireEvent.click(screen.getByRole('button', { name: 'Salvar cliente' }))

    await waitFor(() => expect(customerApi.updateCustomer).toHaveBeenCalled())
    expect(customerApi.updateCustomer).toHaveBeenCalledWith(1, expect.not.objectContaining({ id: 1 }))
    expect(await screen.findByText('Ana Atualizada')).toBeTruthy()
  })

  it('edita fornecedor preservando o CNPJ', async () => {
    render(<SuppliersPage />)
    await screen.findByText('Fornecedor A')
    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
    fireEvent.change(screen.getByLabelText('Nome'), { target: { value: 'Fornecedor Atualizado' } })
    fireEvent.click(screen.getByRole('button', { name: 'Salvar fornecedor' }))

    await waitFor(() => expect(supplierApi.updateSupplier).toHaveBeenCalled())
    expect(supplierApi.updateSupplier).toHaveBeenCalledWith(2, expect.objectContaining({ cnpj: supplier.cnpj }))
    expect(supplierApi.updateSupplier).toHaveBeenCalledWith(2, expect.not.objectContaining({ id: 2 }))
  })

  it('edita funcionário mantendo RG e complemento nulos', async () => {
    render(<EmployeesPage />)
    await screen.findByText('Carlos Souza')
    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
    fireEvent.click(screen.getByRole('button', { name: 'Salvar funcionário' }))

    await waitFor(() => expect(employeeApi.updateEmployee).toHaveBeenCalled())
    expect(employeeApi.updateEmployee).toHaveBeenCalledWith(4, expect.objectContaining({ rg: null, complemento: null }))
    expect(employeeApi.updateEmployee).toHaveBeenCalledWith(4, expect.not.objectContaining({ id: 4 }))
  })

  it('permite desativar funcionário e mostra o novo status', async () => {
    vi.mocked(employeeApi.updateEmployee).mockResolvedValue({ ...employee, ativo: false })
    render(<EmployeesPage />)
    await screen.findByText('Carlos Souza')
    expect(screen.getByText('Ativo')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
    fireEvent.change(screen.getByLabelText('Status'), { target: { value: 'inactive' } })
    fireEvent.click(screen.getByRole('button', { name: 'Salvar funcionário' }))

    await waitFor(() => expect(employeeApi.updateEmployee).toHaveBeenCalledWith(4, expect.objectContaining({ ativo: false })))
    expect(screen.getByText('Inativo')).toBeTruthy()
    expect(screen.getByText('Funcionário atualizado com sucesso.')).toBeTruthy()
  })

  it('edita preço e fornecedor do produto preservando os decimais', async () => {
    render(<ProductsPage />)
    await screen.findByText('Produto A')
    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
    fireEvent.change(screen.getByLabelText('Preço de venda'), { target: { value: '19.00' } })
    fireEvent.change(screen.getByLabelText('Fornecedor'), { target: { value: String(secondSupplier.id) } })
    fireEvent.click(screen.getByRole('button', { name: 'Salvar produto' }))

    await waitFor(() => expect(productApi.updateProduct).toHaveBeenCalled())
    expect(productApi.updateProduct).toHaveBeenCalledWith(5, expect.objectContaining({ preco_venda: '19.00', fornecedor_id: 3 }))
    expect(productApi.updateProduct).toHaveBeenCalledWith(5, expect.not.objectContaining({ id: 5 }))
  })
})
