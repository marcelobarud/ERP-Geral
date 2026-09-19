// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import * as reportsApi from './api'
import { CommercialReportPage } from './ReportsPages'

vi.mock('./api', () => ({
  getCommercialReport: vi.fn(),
  getErpDashboard: vi.fn(),
  getFinanceReport: vi.fn(),
  getPurchasesReport: vi.fn(),
  getStockReport: vi.fn(),
}))

afterEach(cleanup)

const report = {
  sales: 3,
  completed_sales: 2,
  cancelled_sales: 1,
  approved_returns: 1,
  granularity: 'month' as const,
  sales_trend: [
    { bucket: '2026-08-01', sales_value: 50, completed_sales: 1 },
    { bucket: '2026-09-01', sales_value: 75, completed_sales: 1 },
  ],
  by_customer: [{ customer_id: 4, customer_name: 'Cliente analytics', sales: 2, total: 125 }],
  by_product: [{ product_id: 8, product_name: 'Produto analytics', quantity: 3.5, total: 125 }],
}

describe('CommercialReportPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(reportsApi.getCommercialReport).mockResolvedValue(report)
  })

  it('organizes scope, metrics and detailed evidence without changing report data', async () => {
    render(<CommercialReportPage />)

    expect(await screen.findByRole('heading', { name: 'Estado comercial' })).toBeTruthy()
    expect(screen.getAllByText('Período: todo o histórico')).toHaveLength(2)
    const returnsMetric = screen.getByText('Devoluções aprovadas').closest('article')
    expect(returnsMetric?.textContent).toContain('Todo o histórico')
    expect(returnsMetric?.textContent).toContain('1')
    expect(screen.getByText('Vendas por produto')).toBeTruthy()
    expect(screen.getAllByText('Produto analytics')).toHaveLength(2)
    expect(screen.getAllByText('Cliente analytics')).toHaveLength(2)
    expect(screen.getByText('3,5')).toBeTruthy()
    expect(screen.getByRole('heading', { name: 'Vendas ao longo do período' })).toBeTruthy()
    expect(screen.getByLabelText('Gráfico de linha com a evolução das vendas concluídas')).toBeTruthy()
    expect(screen.getByLabelText('Gráfico de barras com os produtos que mais contribuíram')).toBeTruthy()
    expect(screen.getByLabelText('Gráfico de barras com os clientes que mais contribuíram')).toBeTruthy()
    expect((screen.getByRole('button', { name: 'Exportar CSV' }) as HTMLButtonElement).disabled).toBe(false)

    fireEvent.change(screen.getByLabelText('De'), { target: { value: '2026-09-01' } })

    await waitFor(() => expect(reportsApi.getCommercialReport).toHaveBeenCalledWith({ dateFrom: '2026-09-01', dateTo: '' }))
    expect(screen.getAllByText('Período: desde 01/09/2026')).toHaveLength(2)
  })

  it('distinguishes a natural empty period and disables export without rows', async () => {
    vi.mocked(reportsApi.getCommercialReport).mockResolvedValue({
      sales: 0,
      completed_sales: 0,
      cancelled_sales: 0,
      approved_returns: 0,
      granularity: 'month',
      sales_trend: [],
      by_customer: [],
      by_product: [],
    })

    render(<CommercialReportPage />)

    expect(await screen.findByText('Não houve vendas no período selecionado')).toBeTruthy()
    expect((screen.getByRole('button', { name: 'Exportar CSV' }) as HTMLButtonElement).disabled).toBe(true)
    expect(screen.queryByText('Vendas por produto')).toBeNull()
  })

  it('keeps charts contextual when only cancelled sales exist', async () => {
    vi.mocked(reportsApi.getCommercialReport).mockResolvedValue({
      sales: 1,
      completed_sales: 0,
      cancelled_sales: 1,
      approved_returns: 0,
      granularity: 'day',
      sales_trend: [{ bucket: '2026-09-01', sales_value: 0, completed_sales: 0 }],
      by_customer: [],
      by_product: [],
    })

    render(<CommercialReportPage />)

    expect(await screen.findByText('Sem vendas concluídas para traçar a evolução')).toBeTruthy()
    expect(screen.getByText('Sem agregação por produto')).toBeTruthy()
    expect(screen.getByText('Sem agregação por cliente')).toBeTruthy()
  })

  it('keeps the report context during loading and offers retry after an error', async () => {
    let resolveReport: ((value: typeof report) => void) | undefined
    vi.mocked(reportsApi.getCommercialReport).mockImplementationOnce(() => new Promise((resolve) => { resolveReport = resolve }))

    render(<CommercialReportPage />)

    expect(screen.getByRole('heading', { name: 'Relatório comercial' })).toBeTruthy()
    expect(screen.getByLabelText('De')).toBeTruthy()
    expect(screen.getByRole('status')).toBeTruthy()
    resolveReport?.(report)
    expect(await screen.findByRole('heading', { name: 'Vendas por produto' })).toBeTruthy()

    vi.mocked(reportsApi.getCommercialReport).mockRejectedValueOnce(new Error('API indisponível'))
    fireEvent.change(screen.getByLabelText('De'), { target: { value: '2030-01-01' } })
    expect(await screen.findByRole('alert')).toBeTruthy()
    expect(screen.getByRole('heading', { name: 'Relatório comercial' })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Tentar novamente' }))
    expect(await screen.findByRole('heading', { name: 'Vendas por produto' })).toBeTruthy()
  })
})
