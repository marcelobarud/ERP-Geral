// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import * as reportsApi from './api'
import { CommercialReportPage, FinanceReportPage, PurchasesReportPage, StockReportPage } from './ReportsPages'

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

  it('keeps detailed tables complete when charts are limited to six items', async () => {
    vi.mocked(reportsApi.getCommercialReport).mockResolvedValue({
      ...report,
      by_product: Array.from({ length: 7 }, (_, index) => ({
        product_id: index + 1,
        product_name: `Produto detalhado ${index + 1}`,
        quantity: index + 1,
        total: (index + 1) * 10,
      })),
      by_customer: Array.from({ length: 7 }, (_, index) => ({
        customer_id: index + 1,
        customer_name: `Cliente detalhado ${index + 1}`,
        sales: index + 1,
        total: (index + 1) * 10,
      })),
    })

    render(<CommercialReportPage />)

    expect(await screen.findAllByText('Produto detalhado 7')).toHaveLength(2)
    expect(screen.getAllByText('Cliente detalhado 7')).toHaveLength(2)
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

const purchasesReport = {
  total_orders: 1,
  pending_receipts: 0,
  quotes: 1,
  period: '12m' as const,
  date_from: '2025-09-20',
  date_to: '2026-09-19',
  period_orders: 1,
  received_orders_in_period: 1,
  confirmed_receipts_in_period: 2,
  ordered_value_in_period: 85,
  received_value_in_period: 85,
  open_orders: 0,
  pending_value: 0,
  pending_line_count: 0,
  status_counts: { RASCUNHO: 0, EMITIDO: 0, PARCIALMENTE_RECEBIDO: 0, RECEBIDO: 1, CANCELADO: 0 },
  orders: [{ id: 1, numero: 'PC-001', supplier_name: 'Fornecedor analytics', status: 'RECEBIDO' as const, created_at: '2026-09-11', ordered_value: 85, pending_value: 0 }],
}

describe('PurchasesReportPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(reportsApi.getPurchasesReport).mockImplementation(async (period = '12m') => ({
      ...purchasesReport,
      period,
      date_from: period === '30d' ? '2026-08-21' : purchasesReport.date_from,
    }))
  })

  it('separates period activity from current purchase position without forcing charts', async () => {
    render(<PurchasesReportPage />)

    expect(await screen.findByRole('heading', { name: 'Compras no período' })).toBeTruthy()
    expect(screen.getByText('Pedidos no período')).toBeTruthy()
    expect(screen.getByText('Pedidos em aberto')).toBeTruthy()
    expect(screen.getAllByText('R$ 85,00').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Nenhum recebimento pendente')).toBeTruthy()
    expect(screen.getByRole('heading', { name: 'Distribuição por status' })).toBeTruthy()
    expect(screen.getByRole('table', { name: 'Pedidos de compra criados no período' })).toBeTruthy()
    expect(screen.queryByRole('heading', { name: 'Evolução das compras' })).toBeNull()

    fireEvent.change(screen.getByLabelText('Período da atividade'), { target: { value: '30d' } })

    await waitFor(() => expect(reportsApi.getPurchasesReport).toHaveBeenCalledWith('30d'))
    expect(await screen.findByText('Últimos 30 dias: 21/08/2026 a 19/09/2026')).toBeTruthy()
  })

  it('renders pending receipt attention with monetary evidence', async () => {
    vi.mocked(reportsApi.getPurchasesReport).mockResolvedValue({
      ...purchasesReport,
      pending_receipts: 1,
      open_orders: 1,
      pending_value: 51,
      pending_line_count: 1,
      status_counts: { RASCUNHO: 0, EMITIDO: 0, PARCIALMENTE_RECEBIDO: 1, RECEBIDO: 0, CANCELADO: 0 },
      orders: [{ ...purchasesReport.orders[0], status: 'PARCIALMENTE_RECEBIDO', pending_value: 51 }],
    })

    render(<PurchasesReportPage />)

    expect(await screen.findByText('Recebimentos pendentes')).toBeTruthy()
    expect(screen.getByText('Valor pendente')).toBeTruthy()
    expect(screen.getAllByText('R$ 51,00').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Parcialmente recebido').length).toBeGreaterThanOrEqual(1)
  })

  it('communicates a naturally empty period and preserves context during loading/error', async () => {
    vi.mocked(reportsApi.getPurchasesReport).mockResolvedValue({
      ...purchasesReport,
      period_orders: 0,
      received_orders_in_period: 0,
      confirmed_receipts_in_period: 0,
      ordered_value_in_period: 0,
      received_value_in_period: 0,
      status_counts: { RASCUNHO: 0, EMITIDO: 0, PARCIALMENTE_RECEBIDO: 0, RECEBIDO: 0, CANCELADO: 0 },
      orders: [],
    })

    render(<PurchasesReportPage />)

    expect(await screen.findByText('Nenhum pedido no período selecionado. Ajuste a janela para investigar outra atividade.')).toBeTruthy()
    expect((screen.getByRole('button', { name: 'Exportar CSV' }) as HTMLButtonElement).disabled).toBe(true)

    let rejectReport: ((reason?: unknown) => void) | undefined
    vi.mocked(reportsApi.getPurchasesReport).mockImplementationOnce(() => new Promise((_resolve, reject) => { rejectReport = reject }))
    fireEvent.change(screen.getByLabelText('Período da atividade'), { target: { value: '30d' } })
    expect(screen.getByRole('status')).toBeTruthy()
    rejectReport?.(new Error('API indisponível'))
    expect(await screen.findByRole('alert')).toBeTruthy()
    expect(screen.getByRole('heading', { name: 'Relatório de compras' })).toBeTruthy()
    expect(screen.getByLabelText('Período da atividade')).toBeTruthy()
  })
})

const criticalStockBalance = {
  produto_id: 1,
  deposito_id: 1,
  saldo: '3.125',
  estoque_minimo: '10.000',
  abaixo_do_minimo: true,
  product_name: 'Produto crítico com nome operacional muito longo',
  sku: 'CRITICO-001',
  unit: 'UN',
  deficit: '6.875',
  shortfall_percent: 68.75,
}

const normalStockBalance = {
  produto_id: 2,
  deposito_id: 1,
  saldo: '10.000',
  estoque_minimo: '0.000',
  abaixo_do_minimo: false,
  product_name: 'Produto normal',
  sku: 'NORMAL-002',
  unit: 'KG',
  deficit: '0.000',
  shortfall_percent: null,
}

const stockReport = {
  balances: [criticalStockBalance, normalStockBalance],
  below_minimum: [criticalStockBalance],
  movement_count: 9,
  active_products: 2,
  products_with_balance: 2,
  period: '12m' as const,
  date_from: '2025-09-20',
  date_to: '2026-09-19',
  granularity: 'month' as const,
  movement_entries: 4,
  movement_exits: 2,
  movement_count_in_period: 6,
  movement_series: [
    { bucket: '2026-08-01', entries: 1, exits: 0 },
    { bucket: '2026-09-01', entries: 3, exits: 2 },
  ],
  deposit: { id: 1, code: 'PRINCIPAL', name: 'Depósito principal' },
}

describe('StockReportPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(reportsApi.getStockReport).mockImplementation(async (period = '12m') => ({
      ...stockReport,
      period,
      date_from: period === '30d' ? '2026-08-21' : stockReport.date_from,
      granularity: period === '30d' ? 'day' : stockReport.granularity,
    }))
  })

  it('separates current position from movement period and preserves detailed quantities', async () => {
    render(<StockReportPage />)

    expect(await screen.findByRole('heading', { name: 'Estoque no depósito' })).toBeTruthy()
    expect(screen.getByText('Produtos com saldo')).toBeTruthy()
    expect(screen.getByRole('heading', { name: 'Movimentações ao longo do período' })).toBeTruthy()
    expect(screen.getByLabelText('Gráfico de barras com entradas e saídas de estoque ao longo do período')).toBeTruthy()
    expect(screen.getByLabelText('Gráfico de barras com produtos abaixo do estoque mínimo')).toBeTruthy()
    expect(screen.getAllByText('Produto crítico com nome operacional muito longo')).toHaveLength(1)
    expect(screen.getByText('3,125 UN')).toBeTruthy()
    expect(screen.getByText('10 KG')).toBeTruthy()
    expect(screen.getByRole('table', { name: 'Saldos atuais agrupados por produto' })).toBeTruthy()

    fireEvent.change(screen.getByLabelText('Período das movimentações'), { target: { value: '30d' } })

    await waitFor(() => expect(reportsApi.getStockReport).toHaveBeenCalledWith('30d'))
    expect(await screen.findByText('Últimos 30 dias: 21/08/2026 a 19/09/2026')).toBeTruthy()
  })

  it('uses specific empty states for temporal data and healthy stock', async () => {
    vi.mocked(reportsApi.getStockReport).mockResolvedValue({
      ...stockReport,
      below_minimum: [],
      movement_entries: 0,
      movement_exits: 0,
      movement_count_in_period: 0,
      movement_series: stockReport.movement_series.map((point) => ({ ...point, entries: 0, exits: 0 })),
    })

    render(<StockReportPage />)

    expect(await screen.findByText('Nenhuma movimentação no período selecionado')).toBeTruthy()
    expect(screen.getByText('Estoque dentro do mínimo')).toBeTruthy()
    expect(screen.queryByLabelText('Gráfico de barras com entradas e saídas de estoque ao longo do período')).toBeNull()
  })

  it.each([
    { entries: 2, exits: 0 },
    { entries: 0, exits: 2 },
  ])('renders a sparse chart with directional data %#', async ({ entries, exits }) => {
    vi.mocked(reportsApi.getStockReport).mockResolvedValue({
      ...stockReport,
      movement_entries: entries,
      movement_exits: exits,
      movement_count_in_period: entries + exits,
      movement_series: [{ bucket: '2026-09-01', entries, exits }],
    })

    render(<StockReportPage />)

    expect(await screen.findByLabelText('Gráfico de barras com entradas e saídas de estoque ao longo do período')).toBeTruthy()
  })

  it('preserves header and period during loading and errors', async () => {
    let rejectReport: ((reason?: unknown) => void) | undefined
    vi.mocked(reportsApi.getStockReport).mockImplementationOnce(() => new Promise((_resolve, reject) => { rejectReport = reject }))

    render(<StockReportPage />)

    expect(screen.getByRole('heading', { name: 'Relatório de estoque' })).toBeTruthy()
    expect(screen.getByLabelText('Período das movimentações')).toBeTruthy()
    expect(screen.getByRole('status')).toBeTruthy()
    rejectReport?.(new Error('API indisponível'))
    expect(await screen.findByRole('alert')).toBeTruthy()
    expect(screen.getByLabelText('Período das movimentações')).toBeTruthy()
  })
})

const financeReport = {
  previsto_receber: '4200.00',
  previsto_pagar: '1700.00',
  realizado_receber: '3100.00',
  realizado_pagar: '1250.00',
  receivable_titles: 12,
  payable_titles: 7,
  overdue_installments: 3,
  overdue_open_installments: 2,
  overdue_receivable: 620,
  overdue_payable: 180,
  period: '12m' as const,
  date_from: '2025-09-20',
  date_to: '2026-09-19',
  granularity: 'month' as const,
  commitments: [
    { bucket: '2026-08-01', receivable: 900, payable: 500 },
    { bucket: '2026-09-01', receivable: 1200, payable: 650 },
  ],
}

describe('FinanceReportPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(reportsApi.getFinanceReport).mockImplementation(async (period = '12m') => ({
      ...financeReport,
      period,
      date_from: period === '90d' ? '2026-06-22' : financeReport.date_from,
      granularity: period === '90d' ? 'week' : financeReport.granularity,
    }))
  })

  it('separates the accumulated position from commitments in the selected period', async () => {
    render(<FinanceReportPage />)

    expect(await screen.findByRole('heading', { name: 'Saldos e liquidações' })).toBeTruthy()
    expect(screen.getAllByText('A receber em aberto')).toHaveLength(2)
    expect(screen.getByText('Pago')).toBeTruthy()
    expect(screen.getByLabelText('Quantidade de títulos financeiros').textContent).toContain('12 títulos a receber')
    expect(screen.getByRole('heading', { name: 'Compromissos por vencimento' })).toBeTruthy()
    expect(screen.getByLabelText('Gráfico de barras com valores a receber e a pagar em aberto por vencimento')).toBeTruthy()
    const overduePanel = screen.getByText('Parcelas vencidas ainda em aberto').closest('article')
    expect(overduePanel?.textContent).toContain('800,00')
    expect((screen.getByRole('button', { name: 'Exportar CSV' }) as HTMLButtonElement).disabled).toBe(false)

    fireEvent.change(screen.getByLabelText('Período dos vencimentos'), { target: { value: '90d' } })

    await waitFor(() => expect(reportsApi.getFinanceReport).toHaveBeenCalledWith('90d'))
    expect(await screen.findByText('Últimas 12 semanas: 22/06/2026 a 19/09/2026')).toBeTruthy()
  })

  it('uses contextual empty states instead of rendering empty axes or false alerts', async () => {
    vi.mocked(reportsApi.getFinanceReport).mockResolvedValue({
      ...financeReport,
      previsto_receber: '0.00',
      previsto_pagar: '0.00',
      realizado_receber: '0.00',
      realizado_pagar: '0.00',
      receivable_titles: 0,
      payable_titles: 0,
      overdue_installments: 0,
      overdue_open_installments: 0,
      overdue_receivable: 0,
      overdue_payable: 0,
      commitments: [
        { bucket: '2026-08-01', receivable: 0, payable: 0 },
        { bucket: '2026-09-01', receivable: 0, payable: 0 },
      ],
    })

    render(<FinanceReportPage />)

    expect(await screen.findByText('Nenhum compromisso em aberto neste período')).toBeTruthy()
    expect(screen.getByText('Nenhuma parcela vencida em aberto')).toBeTruthy()
    expect(screen.queryByLabelText('Gráfico de barras com valores a receber e a pagar em aberto por vencimento')).toBeNull()
  })

  it('preserves the page header and period control during loading and errors', async () => {
    let rejectReport: ((reason?: unknown) => void) | undefined
    vi.mocked(reportsApi.getFinanceReport).mockImplementationOnce(() => new Promise((_resolve, reject) => { rejectReport = reject }))

    render(<FinanceReportPage />)

    expect(screen.getByRole('heading', { name: 'Relatório financeiro' })).toBeTruthy()
    expect(screen.getByLabelText('Período dos vencimentos')).toBeTruthy()
    expect(screen.getByRole('status')).toBeTruthy()
    rejectReport?.(new Error('API indisponível'))
    expect(await screen.findByRole('alert')).toBeTruthy()
    expect(screen.getByLabelText('Período dos vencimentos')).toBeTruthy()
  })
})
