// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../services/httpClient'
import * as dashboardApi from './api'
import { DashboardPage } from './DashboardPage'

vi.mock('./api', () => ({ getDashboardSummary: vi.fn() }))

describe('DashboardPage', () => {
  afterEach(() => cleanup())

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(dashboardApi.getDashboardSummary).mockResolvedValue({ customers: 0, products: 0, suppliers: 0, employees: 0, sales: 0 })
  })

  it('loads and renders operational counts and all shortcuts', async () => {
    vi.mocked(dashboardApi.getDashboardSummary).mockResolvedValue({ customers: 2, products: 3, suppliers: 1, employees: 4, sales: 5 })
    const onNavigate = vi.fn()

    render(<DashboardPage onNavigate={onNavigate} />)

    expect(await screen.findByText('Resumo operacional')).toBeTruthy()
    expect(screen.getByRole('link', { name: /Clientes/ }).textContent).toContain('2')
    expect(screen.getByRole('link', { name: /Produtos/ }).textContent).toContain('3')
    expect(screen.getByRole('link', { name: /Fornecedores/ }).textContent).toContain('1')
    expect(screen.getByRole('link', { name: /Funcionários/ }).textContent).toContain('4')
    expect(screen.getByRole('link', { name: /Vendas/ }).textContent).toContain('5')
    expect(screen.getByRole('link', { name: /Nova vendaRegistre uma venda com um ou mais produtos/ })).toBeTruthy()

    const sections = Array.from(document.querySelectorAll('.dashboard-section'))
    expect(sections[0]?.classList.contains('dashboard-actions-section')).toBe(true)
    expect(sections[1]?.querySelector('#dashboard-summary-title')).toBeTruthy()
  })

  it('shows a consistent loading state while list requests are pending', () => {
    vi.mocked(dashboardApi.getDashboardSummary).mockImplementation(() => new Promise<never>(() => {}))

    render(<DashboardPage onNavigate={vi.fn()} />)

    expect(screen.getByRole('status').textContent).toContain('Carregando resumo operacional...')
    expect(screen.queryByText('Resumo operacional')).toBeNull()
  })

  it('renders zero counts when all lists are empty', async () => {
    render(<DashboardPage onNavigate={vi.fn()} />)

    await screen.findByText('Resumo operacional')
    expect(screen.getAllByText('0')).toHaveLength(5)
    expect(screen.getByText('Nenhum cliente cadastrado')).toBeTruthy()
    expect(screen.getByText('Nenhuma venda registrada')).toBeTruthy()
  })

  it('shows a retryable message when one list request fails', async () => {
    vi.mocked(dashboardApi.getDashboardSummary).mockRejectedValue(new ApiError(503, 'Backend indisponível.'))
    render(<DashboardPage onNavigate={vi.fn()} />)

    expect(await screen.findByText('Algumas informações não puderam ser carregadas. Tente novamente.')).toBeTruthy()
    expect(screen.getAllByText('—')).toHaveLength(5)

    vi.mocked(dashboardApi.getDashboardSummary).mockResolvedValue({ customers: 0, products: 0, suppliers: 0, employees: 0, sales: 0 })
    fireEvent.click(screen.getByRole('button', { name: 'Tentar novamente' }))

    await waitFor(() => expect(dashboardApi.getDashboardSummary).toHaveBeenCalledTimes(2))
    expect(await screen.findByText('Nenhum produto cadastrado')).toBeTruthy()
  })

  it('uses the existing in-app navigation callback from shortcut links', async () => {
    const onNavigate = vi.fn()
    render(<DashboardPage onNavigate={onNavigate} />)
    await screen.findByText('Resumo operacional')

    fireEvent.click(screen.getByRole('link', { name: /Clientes/ }))
    fireEvent.click(screen.getByRole('link', { name: /Nova vendaRegistre uma venda com um ou mais produtos/ }))

    expect(onNavigate).toHaveBeenNthCalledWith(1, '/customers')
    expect(onNavigate).toHaveBeenNthCalledWith(2, '/sales/new')
  })
})
