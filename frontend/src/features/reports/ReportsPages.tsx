import { useCallback, useEffect, useState, type ReactNode } from 'react'

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

function quantity(value: number) {
  return new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 3 }).format(value || 0)
}

function formatDate(value: string) {
  const [year, month, day] = value.split('-')
  return `${day}/${month}/${year}`
}

function formatPeriod(filters: ReportFilters) {
  if (filters.dateFrom && filters.dateTo) return `Período: ${formatDate(filters.dateFrom)} a ${formatDate(filters.dateTo)}`
  if (filters.dateFrom) return `Período: desde ${formatDate(filters.dateFrom)}`
  if (filters.dateTo) return `Período: até ${formatDate(filters.dateTo)}`
  return 'Período: todo o histórico'
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
  return <form className="report-filter-bar" onSubmit={(event) => { event.preventDefault(); onSubmit() }}><label>De<input type="date" value={filters.dateFrom} onChange={(event) => onChange({ ...filters, dateFrom: event.target.value })} /></label><label>Até<input type="date" value={filters.dateTo} onChange={(event) => onChange({ ...filters, dateTo: event.target.value })} /></label><button className="button button-primary" type="submit">Aplicar</button></form>
}

export function ErpDashboardPage() {
  const [data, setData] = useState<ErpDashboard | null>(null)
  const [error, setError] = useState<string | null>(null)
  const load = useCallback(async () => { try { setError(null); setData(await getErpDashboard()) } catch (cause) { setError(getApiErrorMessage(cause, 'Não foi possível carregar o dashboard ERP.')) } }, [])
  useEffect(() => { void load() }, [load])
  return <div className="dashboard-page"><PageHeader eyebrow="Relatórios" title="Dashboard ERP" description="Acompanhe os principais indicadores comerciais, operacionais e financeiros." pageId="reports_dashboard" />{!data && !error ? <LoadingState label="Carregando indicadores ERP..." /> : null}{error ? <ErrorState description={error} onRetry={() => void load()} /> : null}{data ? <div className="report-metrics-grid"><Metric label="Clientes" value={data.customers} /><Metric label="Produtos ativos" value={data.products} /><Metric label="Vendas concluídas" value={data.completed_sales} /><Metric label="Produtos abaixo do mínimo" value={data.low_stock_products} /><Metric label="A receber em aberto" value={money(data.receivable_open)} /><Metric label="A pagar em aberto" value={money(data.payable_open)} /><Metric label="Recebido" value={money(data.realized_receivable)} /><Metric label="Pago" value={money(data.realized_payable)} /></div> : null}</div>
}

export function CommercialReportPage() {
  const [filters, setFilters] = useState(initialFilters)
  const [data, setData] = useState<CommercialReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const load = useCallback(async () => { try { setError(null); setData(await getCommercialReport(filters)) } catch (cause) { setError(getApiErrorMessage(cause, 'Não foi possível carregar o relatório comercial.')) } }, [filters])
  useEffect(() => { void load() }, [load])
  const rows = data && data.sales > 0 ? [{ produto: 'Resumo', quantidade: data.completed_sales, total: data.sales }, ...data.by_product.map((item) => ({ produto: item.product_id, quantidade: item.quantity, total: item.total }))] : []
  const hasPeriodFilter = Boolean(filters.dateFrom || filters.dateTo)
  return <ReportLayout pageId="reports_commercial" loaded={data !== null} eyebrow="Relatórios" title="Relatório comercial" description="Vendas, cancelamentos, devoluções e agregações por produto." filters={filters} setFilters={setFilters} onSubmit={() => void load()} rows={rows} filename="relatorio-comercial.csv" error={error} onRetry={() => void load()} emptyTitle={hasPeriodFilter ? 'Nenhuma venda encontrada neste recorte' : 'Não houve vendas no período selecionado'} emptyDescription={hasPeriodFilter ? 'Ajuste ou remova o período para ampliar a análise.' : 'Selecione um período para investigar outra janela de vendas.'}><CommercialReportContent data={data} filters={filters} /></ReportLayout>
}

function CommercialReportContent({ data, filters }: { data: CommercialReport | null; filters: ReportFilters }) {
  if (!data) return null

  return (
    <>
      <section className="report-metric-group" aria-labelledby="commercial-metrics-title">
        <div className="report-section-heading">
          <div>
            <p className="eyebrow">Resumo do período</p>
            <h2 id="commercial-metrics-title">Estado comercial</h2>
          </div>
          <p className="report-section-context">{formatPeriod(filters)}</p>
        </div>
        <div className="report-metric-layout">
          <article className="report-primary-metric">
            <span className="dashboard-card-label">Vendas no período</span>
            <strong className="report-primary-metric-value">{data.sales}</strong>
            <span className="dashboard-card-description">Vendas registradas no recorte selecionado.</span>
          </article>
          <div className="report-supporting-metrics">
            <Metric label="Concluídas" value={data.completed_sales} detail="Status concluída" />
            <Metric label="Canceladas" value={data.cancelled_sales} detail="Status cancelada" />
            <Metric label="Devoluções aprovadas" value={data.approved_returns} detail="Todo o histórico" />
          </div>
        </div>
      </section>

      <section className="report-analysis-section" aria-labelledby="commercial-products-title">
        <div className="report-section-heading">
          <div>
            <p className="eyebrow">Evidência principal</p>
            <h2 id="commercial-products-title">Vendas por produto</h2>
            <p>Compare quantidade e valor das vendas concluídas no período.</p>
          </div>
        </div>
        {data.by_product.length ? <CommercialProductsTable items={data.by_product} /> : <div className="data-card report-detail-empty"><p>Não há vendas concluídas para detalhar neste recorte.</p></div>}
      </section>

      <section className="report-supporting-section" aria-labelledby="commercial-customers-title">
        <div className="report-section-heading">
          <div>
            <p className="eyebrow">Informação de apoio</p>
            <h2 id="commercial-customers-title">Vendas por cliente</h2>
            <p>Use esta lista para investigar quais clientes compõem o resultado.</p>
          </div>
        </div>
        {data.by_customer.length ? <CommercialCustomersTable items={data.by_customer} /> : <div className="data-card report-detail-empty"><p>Não há vendas concluídas por cliente para este recorte.</p></div>}
      </section>
    </>
  )
}

function CommercialProductsTable({ items }: { items: CommercialReport['by_product'] }) {
  return <div className="data-card report-detail-table"><div className="data-table-wrap"><table className="data-table"><caption className="sr-only">Vendas concluídas agrupadas por produto</caption><thead><tr><th scope="col">Produto</th><th scope="col">Quantidade</th><th scope="col">Total</th></tr></thead><tbody>{items.map((item) => <tr key={item.product_id}><td className="data-primary">Produto #{item.product_id}</td><td className="report-number-cell">{quantity(item.quantity)}</td><td className="report-number-cell">{money(item.total)}</td></tr>)}</tbody></table></div></div>
}

function CommercialCustomersTable({ items }: { items: CommercialReport['by_customer'] }) {
  return <div className="data-card report-detail-table"><div className="data-table-wrap"><table className="data-table"><caption className="sr-only">Vendas concluídas agrupadas por cliente</caption><thead><tr><th scope="col">Cliente</th><th scope="col">Vendas</th><th scope="col">Total</th></tr></thead><tbody>{items.map((item, index) => <tr key={item.customer_id ?? `unknown-${index}`}><td className="data-primary">{item.customer_id ? `Cliente #${item.customer_id}` : 'Venda sem cliente'}</td><td className="report-number-cell">{item.sales}</td><td className="report-number-cell">{money(item.total)}</td></tr>)}</tbody></table></div></div>
}

export function PurchasesReportPage() {
  const [data, setData] = useState<PurchasesReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const load = useCallback(async () => { try { setError(null); setData(await getPurchasesReport()) } catch (cause) { setError(getApiErrorMessage(cause, 'Não foi possível carregar o relatório de compras.')) } }, [])
  useEffect(() => { void load() }, [load])
  const rows = data ? [{ pedidos: data.total_orders, recebimentos_pendentes: data.pending_receipts, orcamentos: data.quotes }] : []
  return <ReportLayout pageId="reports_purchases" loaded={data !== null} eyebrow="Relatórios" title="Relatório de compras" description="Acompanhe pedidos, recebimentos pendentes e orçamentos." rows={rows} filename="relatorio-compras.csv" error={error} onRetry={() => void load()}><div className="report-metrics-grid">{data ? <><Metric label="Pedidos" value={data.total_orders} /><Metric label="Recebimentos pendentes" value={data.pending_receipts} /><Metric label="Orçamentos" value={data.quotes} /></> : null}</div></ReportLayout>
}

export function StockReportPage() {
  const [data, setData] = useState<StockReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const load = useCallback(async () => { try { setError(null); setData(await getStockReport()) } catch (cause) { setError(getApiErrorMessage(cause, 'Não foi possível carregar o relatório de estoque.')) } }, [])
  useEffect(() => { void load() }, [load])
  const rows = data ? [{ produto: 'Resumo', quantidade: data.balances.length, abaixo_do_minimo: data.below_minimum.length }, ...data.balances.map((item) => ({ produto: item.produto_id, quantidade: item.quantidade, abaixo_do_minimo: item.abaixo_do_minimo ? 'sim' : 'não' }))] : []
  return <ReportLayout pageId="reports_stock" loaded={data !== null} eyebrow="Relatórios" title="Relatório de estoque" description="Saldos, produtos abaixo do mínimo e movimentações registradas." rows={rows} filename="relatorio-estoque.csv" error={error} onRetry={() => void load()}><div className="report-metrics-grid">{data ? <><Metric label="Itens com saldo" value={data.balances.length} /><Metric label="Abaixo do mínimo" value={data.below_minimum.length} /><Metric label="Movimentações" value={data.movement_count} /></> : null}</div></ReportLayout>
}

export function FinanceReportPage() {
  const [data, setData] = useState<FinanceReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const load = useCallback(async () => { try { setError(null); setData(await getFinanceReport()) } catch (cause) { setError(getApiErrorMessage(cause, 'Não foi possível carregar o relatório financeiro.')) } }, [])
  useEffect(() => { void load() }, [load])
  const rows = data ? [{ contas_a_receber: data.receivable_titles, contas_a_pagar: data.payable_titles, vencidos: data.overdue_installments, previsto_receber: data.previsto_receber, previsto_pagar: data.previsto_pagar }] : []
  return <ReportLayout pageId="reports_finance" loaded={data !== null} eyebrow="Relatórios" title="Relatório financeiro" description="Títulos, vencimentos e fluxo previsto versus realizado." rows={rows} filename="relatorio-financeiro.csv" error={error} onRetry={() => void load()}><div className="report-metrics-grid">{data ? <><Metric label="Contas a receber" value={data.receivable_titles} /><Metric label="Contas a pagar" value={data.payable_titles} /><Metric label="Vencidos" value={data.overdue_installments} /><Metric label="Previsto a receber" value={money(data.previsto_receber)} /><Metric label="Previsto a pagar" value={money(data.previsto_pagar)} /><Metric label="Realizado a receber" value={money(data.realizado_receber)} /></> : null}</div></ReportLayout>
}

function ReportLayout({ pageId, loaded, eyebrow, title, description, filters, setFilters, onSubmit, rows, filename, error, onRetry, emptyTitle = 'Nenhum dado encontrado', emptyDescription = 'Não há registros para os filtros ou período selecionado.', children }: { pageId: string; loaded: boolean; eyebrow: string; title: string; description: string; filters?: ReportFilters; setFilters?: (filters: ReportFilters) => void; onSubmit?: () => void; rows: Array<Record<string, string | number>>; filename: string; error: string | null; onRetry: () => void; emptyTitle?: string; emptyDescription?: string; children: ReactNode }) {
  return <div className="page-stack"><PageHeader eyebrow={eyebrow} title={title} description={description} pageId={pageId} /><div className="report-toolbar"><div>{filters && setFilters && onSubmit ? <FilterBar filters={filters} onChange={setFilters} onSubmit={onSubmit} /> : null}</div><ExportButton rows={rows} filename={filename} /></div>{filters ? <div className="report-active-scope" aria-label={`Escopo ativo: ${formatPeriod(filters)}`}><strong>Escopo ativo</strong><span>{formatPeriod(filters)}</span></div> : null}{error ? <ErrorState description={error} onRetry={onRetry} /> : null}{!error && !loaded ? <LoadingState label="Carregando relatório..." /> : null}{!error && loaded && !rows.length ? <div className="data-card"><EmptyState title={emptyTitle} description={emptyDescription} /></div> : null}{!error && loaded && rows.length ? children : null}</div>
}
