// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../services/httpClient'
import * as employeesApi from './api'
import { EmployeesPage } from './EmployeesPage'

vi.mock('./api', () => ({
  createEmployee: vi.fn(),
  deleteEmployee: vi.fn(),
  listEmployees: vi.fn(),
  updateEmployee: vi.fn(),
}))

const employee = {
  id: 1,
  nome_completo: 'Carlos Souza',
  cidade: 'Santos',
  estado: 'SP',
  rua: 'Rua C',
  numero: '30',
  complemento: null,
  cpf: '123.456.789-09',
  rg: null,
  data_nascimento: '1990-01-01',
  ativo: true,
}

describe('EmployeesPage filter infrastructure pilot', () => {
  afterEach(() => cleanup())

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(employeesApi.listEmployees).mockResolvedValue([employee])
  })

  it('renders an accessible search input and applies normalized search', async () => {
    render(<EmployeesPage />)
    await screen.findByText('Carlos Souza')

    const search = screen.getByRole('searchbox', { name: 'Pesquisar funcionários' })
    fireEvent.change(search, { target: { value: '  Carlos  ' } })
    expect(screen.getByRole('button', { name: 'Limpar pesquisa' })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Filtros' }))
    fireEvent.click(screen.getByRole('button', { name: 'Aplicar filtros' }))

    await waitFor(() => expect(employeesApi.listEmployees).toHaveBeenCalledWith(false, 'Carlos', expect.objectContaining({ page: 1, pageSize: 20 })))
  })

  it('combines search and the existing active filter with AND semantics', async () => {
    render(<EmployeesPage />)
    await screen.findByText('Carlos Souza')

    fireEvent.change(screen.getByRole('searchbox', { name: 'Pesquisar funcionários' }), { target: { value: 'Carlos' } })
    fireEvent.click(screen.getByRole('button', { name: 'Filtros' }))
    expect(screen.getByRole('option', { name: 'Ativos' })).toBeTruthy()
    expect(screen.getByRole('option', { name: 'Inativos' })).toBeTruthy()
    fireEvent.change(screen.getByRole('combobox', { name: 'Status' }), { target: { value: 'active' } })
    fireEvent.click(screen.getByRole('button', { name: 'Aplicar filtros' }))

    await waitFor(() => expect(employeesApi.listEmployees).toHaveBeenCalledWith(true, 'Carlos', expect.objectContaining({ page: 1, pageSize: 20 })))
  })

  it('clears search and active filters back to the unfiltered listing', async () => {
    render(<EmployeesPage />)
    await screen.findByText('Carlos Souza')

    fireEvent.change(screen.getByRole('searchbox', { name: 'Pesquisar funcionários' }), { target: { value: 'Carlos' } })
    fireEvent.click(screen.getByRole('button', { name: 'Filtros' }))
    fireEvent.change(screen.getByRole('combobox', { name: 'Status' }), { target: { value: 'active' } })
    fireEvent.click(screen.getByRole('button', { name: 'Aplicar filtros' }))
    await waitFor(() => expect(employeesApi.listEmployees).toHaveBeenCalledWith(true, 'Carlos', expect.objectContaining({ page: 1, pageSize: 20 })))

    fireEvent.click(screen.getByRole('button', { name: /Filtros \(1\)/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Limpar filtros' }))
    await waitFor(() => expect(employeesApi.listEmployees).toHaveBeenCalledWith(false, '', expect.objectContaining({ page: 1, pageSize: 20 })))
    expect((screen.getByRole('searchbox', { name: 'Pesquisar funcionários' }) as HTMLInputElement).value).toBe('')
    fireEvent.click(screen.getByRole('button', { name: 'Filtros' }))
    expect((screen.getByRole('combobox', { name: 'Status' }) as HTMLSelectElement).value).toBe('all')
  })

  it('distinguishes zero filtered results from an empty base', async () => {
    vi.mocked(employeesApi.listEmployees).mockImplementation(async (_active, search) => search ? [] : [employee])
    render(<EmployeesPage />)
    await screen.findByText('Carlos Souza')

    fireEvent.change(screen.getByRole('searchbox', { name: 'Pesquisar funcionários' }), { target: { value: 'Inexistente' } })
    fireEvent.click(screen.getByRole('button', { name: 'Filtros' }))
    fireEvent.click(screen.getByRole('button', { name: 'Aplicar filtros' }))

    expect(await screen.findByText('Nenhum resultado encontrado para os filtros aplicados.')).toBeTruthy()
  })

  it('keeps loading and retryable error states available', async () => {
    vi.mocked(employeesApi.listEmployees).mockRejectedValueOnce(new ApiError(503, 'Backend indisponível.'))
    render(<EmployeesPage />)
    expect((await screen.findByRole('alert')).textContent).toContain('Backend indisponível.')

    vi.mocked(employeesApi.listEmployees).mockResolvedValue([employee])
    fireEvent.click(screen.getByRole('button', { name: 'Tentar novamente' }))
    expect(await screen.findByText('Carlos Souza')).toBeTruthy()
  })
})
