// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../services/httpClient'
import * as dashboardApi from './api'
import { DashboardPage } from './DashboardPage'

vi.mock('./api', () => ({ getDashboardAnalytics: vi.fn(), getDashboardSummary: vi.fn() }))

const analyticsFixture = {
  period: '12m' as const,
  date_from: '2025-09-18',
  date_to: '2026-09-17',
  granularity: 'month' as const,
  sales_trend: [
    { bucket: '2026-01-01', sales_value: 1200, completed_sales: 4 },
    { bucket: '2026-02-01', sales_value: 1500, completed_sales: 5 },
  ],
  finance_trend: [
    { bucket: '2026-02-01', receivable: 100, payable: 80 },
  ],
  stock_attention: [],
}

describe('DashboardPage', () => {
  afterEach(() => cleanup())

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(dashboardApi.getDashboardSummary).mockResolvedValue({ customers: 0, products: 0, suppliers: 0, employees: 0, sales: 0 })
    vi.mocked(dashboardApi.getDashboardAnalytics).mockResolvedValue(analyticsFixture)
  })

  it('loads and renders operational counts and all shortcuts', async () => {
    vi.mocked(dashboardApi.getDashboardSummary).mockResolvedValue({ customers: 2, products: 3, suppliers: 1, employees: 4, sales: 5 })
    const onNavigate = vi.fn()

    render(<DashboardPage onNavigate={onNavigate} />)

    expect(await screen.findByText('Resumo operacional')).toBeTruthy()
    expect(screen.getByText('Clientes').closest('.dashboard-metric')?.textContent).toContain('2')
    expect(screen.getByText('Produtos').closest('.dashboard-metric')?.textContent).toContain('3')
    expect(screen.getByText('Fornecedores').closest('.dashboard-metric')?.textContent).toContain('1')
    expect(screen.getByText('Funcionários').closest('.dashboard-metric')?.textContent).toContain('4')
    expect(screen.getByText('Vendas').closest('.dashboard-metric')?.textContent).toContain('5')
    expect(screen.getByRole('link', { name: /Nova vendaRegistre uma venda com um ou mais produtos/ })).toBeTruthy()
    expect(screen.getByRole('navigation', { name: 'Atalhos do dashboard' })).toBeTruthy()

    const sections = Array.from(document.querySelectorAll('.dashboard-section'))
    expect(sections[0]?.querySelector('#dashboard-summary-title')).toBeTruthy()
    expect(sections[1]?.classList.contains('dashboard-analytics')).toBe(true)
    expect(sections[2]?.classList.contains('dashboard-actions-section')).toBe(true)
    expect(screen.getByText('Vendas ao longo do tempo')).toBeTruthy()
    expect(screen.getByText('Estoque dentro do mínimo')).toBeTruthy()
  })

  it('shows a consistent loading state while list requests are pending', () => {
    vi.mocked(dashboardApi.getDashboardSummary).mockImplementation(() => new Promise<never>(() => {}))

    render(<DashboardPage onNavigate={vi.fn()} />)

    expect(screen.getByRole('status').textContent).toContain('Carregando resumo operacional...')
    expect(document.querySelector('.dashboard-loading-skeleton')).toBeTruthy()
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

  it('changes only the analytical period and reloads the dashboard analytics', async () => {
    vi.mocked(dashboardApi.getDashboardAnalytics).mockResolvedValue({ ...analyticsFixture, period: '30d', date_from: '2026-08-19', granularity: 'day' })
    render(<DashboardPage onNavigate={vi.fn()} />)

    await screen.findByText('Desempenho recente')
    fireEvent.change(screen.getByRole('combobox', { name: 'Período da análise' }), { target: { value: '30d' } })

    await waitFor(() => expect(dashboardApi.getDashboardAnalytics).toHaveBeenLastCalledWith('30d'))
    expect(screen.getByText('Afeta apenas as visualizações analíticas.')).toBeTruthy()
  })

  it('keeps analytical context visible while chart data is loading', async () => {
    vi.mocked(dashboardApi.getDashboardAnalytics).mockImplementation(() => new Promise<never>(() => {}))
    render(<DashboardPage onNavigate={vi.fn()} />)

    expect(await screen.findByText('Desempenho recente')).toBeTruthy()
    expect(screen.getAllByText('Carregando análise...')).toHaveLength(3)
    expect(screen.getByLabelText('Período da análise')).toBeTruthy()
  })

  it('shows a contextual analytical error with retry', async () => {
    vi.mocked(dashboardApi.getDashboardAnalytics).mockRejectedValue(new ApiError(503, 'Analytics indisponível.'))
    render(<DashboardPage onNavigate={vi.fn()} />)

    expect((await screen.findAllByText('A leitura analítica não pôde ser carregada. Tente novamente.'))).toHaveLength(3)
    const panel = screen.getByRole('heading', { name: 'Vendas ao longo do tempo' }).closest('section')
    expect(panel ? within(panel).getByRole('button', { name: 'Tentar novamente' }) : null).toBeTruthy()
  })

  it('explains empty analytical periods without rendering empty charts', async () => {
    vi.mocked(dashboardApi.getDashboardAnalytics).mockResolvedValue({
      ...analyticsFixture,
      sales_trend: analyticsFixture.sales_trend.map((point) => ({ ...point, sales_value: 0, completed_sales: 0 })),
      finance_trend: analyticsFixture.finance_trend.map((point) => ({ ...point, receivable: 0, payable: 0 })),
    })
    render(<DashboardPage onNavigate={vi.fn()} />)

    expect(await screen.findByText('Nenhuma venda no período')).toBeTruthy()
    expect(screen.getByText('Nenhum compromisso no período')).toBeTruthy()
    expect(screen.getByText('Estoque dentro do mínimo')).toBeTruthy()
    expect(document.querySelectorAll('.dashboard-chart svg')).toHaveLength(0)
  })
})
