import { useCallback, useEffect, useState } from 'react'

import { ErrorState } from '../../components/ErrorState'
import { EmptyState } from '../../components/EmptyState'
import { LoadingState } from '../../components/LoadingState'
import { PageHeader } from '../../components/PageHeader'
import { getApiErrorMessage } from '../../services/httpClient'
import {
  getCommercialReport,
  getErpDashboard,
  getFinanceReport,
  getPurchasesReport,
  getStockReport,
  type CommercialReport,
  type ErpDashboard,
  type FinanceReport,
  type PurchasesReport,
  type StockReport,
} from './api'

type ReportFilters = { dateFrom: string; dateTo: string }

const initialFilters: ReportFilters = { dateFrom: '', dateTo: '' }

function money(value: number) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value || 0)
}

function Metric({ label, value, detail }: { label: string; value: string | number; detail?: string }) {
  return <article className="dashboard-summary-card"><span className="dashboard-card-label">{label}</span><strong className="dashboard-card-value">{value}</strong>{detail ? <span className="dashboard-card-description">{detail}</span> : null}</article>
}

function ExportButton({ rows, filename }: { rows: Array<Record<string, string | number>>; filename: string }) {
  const exportCsv = () => {
    if (!rows.length) return
    const columns = Object.keys(rows[0])
    const csv = [columns.join(';'), ...rows.map((row) => columns.map((column) => JSON.stringify(row[column] ?? '')).join(';'))].join('\n')
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.click()
    URL.revokeObjectURL(url)
  }
  return <button className="button button-secondary" type="button" onClick={exportCsv} disabled={!rows.length}>Exportar CSV</button>
}

function FilterBar({ filters, onChange, onSubmit }: { filters: ReportFilters; onChange: (filters: ReportFilters) => void; onSubmit: () => void }) {
  return <form className="toolbar" onSubmit={(event) => { event.preventDefault(); onSubmit() }}><label>De<input type="date" value={filters.dateFrom} onChange={(event) => onChange({ ...filters, dateFrom: event.target.value })} /></label><label>Até<input type="date" value={filters.dateTo} onChange={(event) => onChange({ ...filters, dateTo: event.target.value })} /></label><button className="button button-primary" type="submit">Aplicar</button></form>
}

export function ErpDashboardPage() {
  const [data, setData] = useState<ErpDashboard | null>(null)
  const [error, setError] = useState<string | null>(null)
  const load = useCallback(async () => { try { setError(null); setData(await getErpDashboard()) } catch (cause) { setError(getApiErrorMessage(cause, 'Não foi possível carregar o dashboard ERP.')) } }, [])
  useEffect(() => { void load() }, [load])
  return <div className="dashboard-page"><PageHeader eyebrow="Relatórios" title="Dashboard ERP" description="Acompanhe os principais indicadores comerciais, operacionais e financeiros." pageId="reports_dashboard" />{!data && !error ? <LoadingState label="Carregando indicadores ERP..." /> : null}{error ? <ErrorState description={error} onRetry={() => void load()} /> : null}{data ? <div className="dashboard-summary-grid"><Metric label="Clientes" value={data.customers} /><Metric label="Produtos ativos" value={data.products} /><Metric label="Vendas concluídas" value={data.completed_sales} /><Metric label="Produtos abaixo do mínimo" value={data.low_stock_products} /><Metric label="A receber em aberto" value={money(data.receivable_open)} /><Metric label="A pagar em aberto" value={money(data.payable_open)} /><Metric label="Recebido" value={money(data.realized_receivable)} /><Metric label="Pago" value={money(data.realized_payable)} /></div> : null}</div>
}

export function CommercialReportPage() {
  const [filters, setFilters] = useState(initialFilters)
  const [data, setData] = useState<CommercialReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const load = useCallback(async () => { try { setError(null); setData(await getCommercialReport(filters)) } catch (cause) { setError(getApiErrorMessage(cause, 'Não foi possível carregar o relatório comercial.')) } }, [filters])
  useEffect(() => { void load() }, [load])
  const rows = data ? [{ produto: 'Resumo', quantidade: data.completed_sales, total: data.sales }, ...data.by_product.map((item) => ({ produto: item.product_id, quantidade: item.quantity, total: item.total }))] : []
  return <ReportLayout pageId="reports_commercial" loaded={data !== null} eyebrow="Relatórios" title="Relatório comercial" description="Vendas, cancelamentos, devoluções e agregações por produto." filters={filters} setFilters={setFilters} onSubmit={() => void load()} rows={rows} filename="relatorio-comercial.csv" error={error} onRetry={() => void load()}><div className="dashboard-summary-grid">{data ? <><Metric label="Vendas no período" value={data.sales} /><Metric label="Concluídas" value={data.completed_sales} /><Metric label="Canceladas" value={data.cancelled_sales} /><Metric label="Devoluções aprovadas" value={data.approved_returns} /></> : null}</div></ReportLayout>
}

export function PurchasesReportPage() {
  const [data, setData] = useState<PurchasesReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const load = useCallback(async () => { try { setError(null); setData(await getPurchasesReport()) } catch (cause) { setError(getApiErrorMessage(cause, 'Não foi possível carregar o relatório de compras.')) } }, [])
  useEffect(() => { void load() }, [load])
  const rows = data ? [{ pedidos: data.total_orders, recebimentos_pendentes: data.pending_receipts, orcamentos: data.quotes }] : []
  return <ReportLayout pageId="reports_purchases" loaded={data !== null} eyebrow="Relatórios" title="Relatório de compras" description="Acompanhe pedidos, recebimentos pendentes e orçamentos." rows={rows} filename="relatorio-compras.csv" error={error} onRetry={() => void load()}><div className="dashboard-summary-grid">{data ? <><Metric label="Pedidos" value={data.total_orders} /><Metric label="Recebimentos pendentes" value={data.pending_receipts} /><Metric label="Orçamentos" value={data.quotes} /></> : null}</div></ReportLayout>
}

export function StockReportPage() {
  const [data, setData] = useState<StockReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const load = useCallback(async () => { try { setError(null); setData(await getStockReport()) } catch (cause) { setError(getApiErrorMessage(cause, 'Não foi possível carregar o relatório de estoque.')) } }, [])
  useEffect(() => { void load() }, [load])
  const rows = data ? [{ produto: 'Resumo', quantidade: data.balances.length, abaixo_do_minimo: data.below_minimum.length }, ...data.balances.map((item) => ({ produto: item.produto_id, quantidade: item.quantidade, abaixo_do_minimo: item.abaixo_do_minimo ? 'sim' : 'não' }))] : []
  return <ReportLayout pageId="reports_stock" loaded={data !== null} eyebrow="Relatórios" title="Relatório de estoque" description="Saldos, produtos abaixo do mínimo e movimentações registradas." rows={rows} filename="relatorio-estoque.csv" error={error} onRetry={() => void load()}><div className="dashboard-summary-grid">{data ? <><Metric label="Itens com saldo" value={data.balances.length} /><Metric label="Abaixo do mínimo" value={data.below_minimum.length} /><Metric label="Movimentações" value={data.movement_count} /></> : null}</div></ReportLayout>
}

export function FinanceReportPage() {
  const [data, setData] = useState<FinanceReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const load = useCallback(async () => { try { setError(null); setData(await getFinanceReport()) } catch (cause) { setError(getApiErrorMessage(cause, 'Não foi possível carregar o relatório financeiro.')) } }, [])
  useEffect(() => { void load() }, [load])
  const rows = data ? [{ contas_a_receber: data.receivable_titles, contas_a_pagar: data.payable_titles, vencidos: data.overdue_installments, previsto_receber: data.previsto_receber, previsto_pagar: data.previsto_pagar }] : []
  return <ReportLayout pageId="reports_finance" loaded={data !== null} eyebrow="Relatórios" title="Relatório financeiro" description="Títulos, vencimentos e fluxo previsto versus realizado." rows={rows} filename="relatorio-financeiro.csv" error={error} onRetry={() => void load()}><div className="dashboard-summary-grid">{data ? <><Metric label="Contas a receber" value={data.receivable_titles} /><Metric label="Contas a pagar" value={data.payable_titles} /><Metric label="Vencidos" value={data.overdue_installments} /><Metric label="Previsto a receber" value={money(data.previsto_receber)} /><Metric label="Previsto a pagar" value={money(data.previsto_pagar)} /><Metric label="Realizado a receber" value={money(data.realizado_receber)} /></> : null}</div></ReportLayout>
}

function ReportLayout({ pageId, loaded, eyebrow, title, description, filters, setFilters, onSubmit, rows, filename, error, onRetry, children }: { pageId: string; loaded: boolean; eyebrow: string; title: string; description: string; filters?: ReportFilters; setFilters?: (filters: ReportFilters) => void; onSubmit?: () => void; rows: Array<Record<string, string | number>>; filename: string; error: string | null; onRetry: () => void; children: React.ReactNode }) {
  return <div className="page-stack"><PageHeader eyebrow={eyebrow} title={title} description={description} pageId={pageId} /><div className="toolbar"><div>{filters && setFilters && onSubmit ? <FilterBar filters={filters} onChange={setFilters} onSubmit={onSubmit} /> : null}</div><ExportButton rows={rows} filename={filename} /></div>{error ? <ErrorState description={error} onRetry={onRetry} /> : null}{!error && !loaded ? <LoadingState label="Carregando relatório..." /> : null}{!error && loaded && !rows.length ? <div className="data-card"><EmptyState title="Nenhum dado encontrado" description="Não há registros para os filtros ou período selecionado." /></div> : null}{!error && loaded && rows.length ? children : null}</div>
}
