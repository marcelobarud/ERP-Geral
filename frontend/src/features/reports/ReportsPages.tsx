import { useCallback, useEffect, useState, type ReactNode } from 'react'

import { BarChart } from '@mui/x-charts/BarChart'
import { LineChart } from '@mui/x-charts/LineChart'

import { ErrorState } from '../../components/ErrorState'
import { EmptyState } from '../../components/EmptyState'
import { LoadingState } from '../../components/LoadingState'
import { PageHeader } from '../../components/PageHeader'
import { actionIcons, iconSizes, iconStroke } from '../../app/iconography'
import { getApiErrorMessage } from '../../services/httpClient'
import {
  chartAxisTickLabelStyle,
  chartSx,
  dashboardPeriodOptions,
  formatBucketLabel,
  formatCompactMoney,
  formatDateRange,
  formatMoney,
  getTickLabelInterval,
  hasPositiveValue,
  type DashboardAnalyticsPeriod,
} from '../dashboard/analytics'
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
import {
  hasPositiveTrend,
  sumTrendSales,
  sumTrendValue,
  topCustomerContributors,
  topProductContributors,
  topStockCriticalItems,
  truncateRankingLabel,
  hasStockMovement,
} from './reportAnalytics'

type ReportFilters = { dateFrom: string; dateTo: string }

const ExportIcon = actionIcons.export

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
  return <button className="button button-secondary" type="button" onClick={exportCsv} disabled={!rows.length}><ExportIcon size={iconSizes.action} stroke={iconStroke} aria-hidden="true" focusable="false" /> Exportar CSV</button>
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

  const salesTrend = data.sales_trend ?? []
  const productItems = topProductContributors(data.by_product)
  const customerItems = topCustomerContributors(data.by_customer)
  const granularity = data.granularity ?? 'month'
  const hasTemporalData = hasPositiveTrend(salesTrend)
  const totalSold = sumTrendValue(salesTrend)
  const completedSales = sumTrendSales(salesTrend)

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

      <section className="report-visual-analysis" aria-labelledby="commercial-analysis-title">
        <div className="report-section-heading">
          <div>
            <p className="eyebrow">Leitura visual</p>
            <h2 id="commercial-analysis-title">Como as vendas se comportaram</h2>
            <p>Use a evolução para entender quando o resultado aconteceu e os rankings para investigar suas principais contribuições.</p>
          </div>
        </div>

        <ReportChartPanel
          id="commercial-sales-trend"
          variant="primary"
          eyebrow="Evolução temporal"
          title="Vendas ao longo do período"
          description="Valor das vendas concluídas no escopo selecionado."
          summary={hasTemporalData ? <div className="report-chart-summary"><div><span>Total vendido</span><strong>{money(totalSold)}</strong></div><div><span>Vendas concluídas</span><strong>{completedSales}</strong></div></div> : null}
          meta={data.granularity ? `Granularidade: ${granularityLabel(granularity)}` : undefined}
        >
          {hasTemporalData ? <div className="report-chart" aria-label="Gráfico de linha com a evolução das vendas concluídas"><LineChart
            xAxis={[{ data: salesTrend.map((point) => point.bucket), scaleType: 'point', tickLabelInterval: getTickLabelInterval(salesTrend.length, granularity), tickLabelStyle: chartAxisTickLabelStyle, valueFormatter: (value: string) => formatBucketLabel(value, granularity) }]}
            yAxis={[{ width: 64, tickLabelStyle: chartAxisTickLabelStyle, valueFormatter: (value: number) => formatCompactMoney(value) }]}
            series={[{ data: salesTrend.map((point) => point.sales_value), label: 'Vendas concluídas', color: 'var(--color-primary)', valueFormatter: (value: number | null) => formatMoney(Number(value)) }]}
            hideLegend
            height={252}
            margin={{ top: 18, right: 18, bottom: 32, left: 8 }}
            grid={{ horizontal: true }}
            sx={chartSx}
          /></div> : <ChartEmptyState title="Sem vendas concluídas para traçar a evolução" description="O recorte possui métricas, mas não há vendas concluídas que alimentem esta série temporal." />}
        </ReportChartPanel>

        <div className="report-ranking-grid">
          <ReportChartPanel
            id="commercial-product-ranking"
            variant="supporting"
            eyebrow="Principais contribuições"
            title="Produtos que mais contribuíram"
            description="Top produtos pelo valor vendido no período."
          >
            {productItems.length ? <CommercialRankingChart items={productItems} kind="product" /> : <ChartEmptyState title="Sem agregação por produto" description="Não há vendas concluídas por produto neste recorte." />}
          </ReportChartPanel>

          <ReportChartPanel
            id="commercial-customer-ranking"
            variant="supporting"
            eyebrow="Principais contribuições"
            title="Clientes que mais contribuíram"
            description="Top clientes pelo valor vendido no período."
          >
            {customerItems.length ? <CommercialRankingChart items={customerItems} kind="customer" /> : <ChartEmptyState title="Sem agregação por cliente" description="Não há vendas concluídas por cliente neste recorte." />}
          </ReportChartPanel>
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

function granularityLabel(granularity: NonNullable<CommercialReport['granularity']>) {
  return { day: 'diária', week: 'semanal', month: 'mensal' }[granularity]
}

function reportTickLabelInterval(pointCount: number, granularity: FinanceReport['granularity']) {
  if (granularity === 'day' && pointCount > 20) {
    return (_value: unknown, index: number) => index % 10 === 0 || index === pointCount - 1
  }
  return getTickLabelInterval(pointCount, granularity)
}

function ChartEmptyState({ title, description }: { title: string; description: string }) {
  return <div className="report-chart-empty"><strong>{title}</strong><p>{description}</p></div>
}

function ReportChartPanel({ id, variant, eyebrow, title, description, summary, meta, children }: { id: string; variant: 'primary' | 'supporting'; eyebrow: string; title: string; description: string; summary?: ReactNode; meta?: string; children: ReactNode }) {
  return <article className={`report-chart-panel report-chart-panel-${variant}`} aria-labelledby={`${id}-title`}><header className="report-chart-panel-header"><div><p className="eyebrow">{eyebrow}</p><h3 id={`${id}-title`}>{title}</h3><p>{description}</p></div>{meta ? <span className="report-chart-meta">{meta}</span> : null}</header><div className="report-chart-panel-body">{summary}{children}</div></article>
}

function CommercialRankingChart(props: { items: ReturnType<typeof topProductContributors>; kind: 'product' } | { items: ReturnType<typeof topCustomerContributors>; kind: 'customer' }) {
  const labels = props.kind === 'product'
    ? props.items.map((item) => item.product_name || `Produto #${item.product_id}`)
    : props.items.map((item) => item.customer_name || (item.customer_id ? `Cliente #${item.customer_id}` : 'Venda sem cliente'))
  const values = props.items.map((item) => item.total)
  const chartHeight = Math.max(176, props.items.length * 30 + 48)
  const labelLimit = props.kind === 'customer' ? 24 : 22
  const labelWidth = props.kind === 'customer' ? 176 : 152
  return <div className="report-chart" aria-label={`Gráfico de barras com ${props.kind === 'product' ? 'os produtos' : 'os clientes'} que mais contribuíram`}><BarChart
    layout="horizontal"
    xAxis={[{ min: 0, tickLabelStyle: { ...chartAxisTickLabelStyle, fontSize: 10 }, valueFormatter: (value: number) => formatCompactMoney(value) }]}
    yAxis={[{ scaleType: 'band', data: labels, tickLabelStyle: chartAxisTickLabelStyle, valueFormatter: (value: string, context) => context.location === 'tooltip' ? value : truncateRankingLabel(value, labelLimit), width: labelWidth }]}
    series={[{ data: values, label: props.kind === 'product' ? 'Valor vendido por produto' : 'Valor vendido por cliente', color: 'var(--color-primary)', valueFormatter: (value: number | null) => formatMoney(Number(value)) }]}
    slotProps={{ tooltip: { trigger: 'axis' } }}
    hideLegend
    height={chartHeight}
    margin={{ top: 12, right: 36, bottom: 32, left: 8 }}
    grid={{ vertical: true }}
    sx={chartSx}
  /></div>
}

function CommercialProductsTable({ items }: { items: CommercialReport['by_product'] }) {
  return <div className="data-card report-detail-table"><div className="data-table-wrap"><table className="data-table"><caption className="sr-only">Vendas concluídas agrupadas por produto</caption><thead><tr><th scope="col">Produto</th><th scope="col">Quantidade</th><th scope="col">Total</th></tr></thead><tbody>{items.map((item) => <tr key={item.product_id}><td className="data-primary">{item.product_name || `Produto #${item.product_id}`}</td><td className="report-number-cell">{quantity(item.quantity)}</td><td className="report-number-cell">{money(item.total)}</td></tr>)}</tbody></table></div></div>
}

function CommercialCustomersTable({ items }: { items: CommercialReport['by_customer'] }) {
  return <div className="data-card report-detail-table"><div className="data-table-wrap"><table className="data-table"><caption className="sr-only">Vendas concluídas agrupadas por cliente</caption><thead><tr><th scope="col">Cliente</th><th scope="col">Vendas</th><th scope="col">Total</th></tr></thead><tbody>{items.map((item, index) => <tr key={item.customer_id ?? `unknown-${index}`}><td className="data-primary">{item.customer_name || (item.customer_id ? `Cliente #${item.customer_id}` : 'Venda sem cliente')}</td><td className="report-number-cell">{item.sales}</td><td className="report-number-cell">{money(item.total)}</td></tr>)}</tbody></table></div></div>
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
  const [period, setPeriod] = useState<DashboardAnalyticsPeriod>('12m')
  const [data, setData] = useState<StockReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const load = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      setData(await getStockReport(period))
    } catch (cause) {
      setError(getApiErrorMessage(cause, 'Não foi possível carregar o relatório de estoque.'))
    } finally {
      setLoading(false)
    }
  }, [period])
  useEffect(() => { void load() }, [load])
  const rows = data ? data.balances.map((item) => ({ produto: item.product_name, sku: item.sku, saldo: item.saldo, estoque_minimo: item.estoque_minimo, unidade: item.unit, abaixo_do_minimo: item.abaixo_do_minimo ? 'sim' : 'não' })) : []
  const selectedPeriodLabel = dashboardPeriodOptions.find((option) => option.value === period)?.label ?? period
  const hasCurrentPeriod = data?.period === period
  const scopeDescription = hasCurrentPeriod
    ? `${selectedPeriodLabel}: ${formatDateRange(data.date_from, data.date_to)}`
    : `${selectedPeriodLabel}: atualizando recorte`

  return <div className="page-stack">
    <PageHeader eyebrow="Relatórios" title="Relatório de estoque" description="Posição atual, movimentações e itens que exigem atenção operacional." pageId="reports_stock" />
    <div className="report-toolbar">
      <label className="dashboard-period-field">
        <span>Período das movimentações</span>
        <select value={period} onChange={(event) => setPeriod(event.target.value as DashboardAnalyticsPeriod)}>
          {dashboardPeriodOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
      </label>
      <ExportButton rows={rows} filename="relatorio-estoque.csv" />
    </div>
    <div className="report-active-scope" aria-label={`Escopo analítico: ${scopeDescription}`}>
      <strong>Escopo analítico</strong>
      <span>{scopeDescription}</span>
      <span>Posição: atual · {data?.deposit.name ?? 'depósito padrão'}</span>
    </div>
    {error ? <ErrorState description={error} onRetry={() => void load()} /> : null}
    {!data && loading ? <LoadingState label="Carregando relatório de estoque..." /> : null}
    {!error && data ? <StockReportContent data={data} selectedPeriod={period} loading={loading} /> : null}
  </div>
}

function StockReportContent({ data, selectedPeriod, loading }: { data: StockReport; selectedPeriod: DashboardAnalyticsPeriod; loading: boolean }) {
  const hasCurrentPeriod = data.period === selectedPeriod
  const movementSeries = hasCurrentPeriod ? data.movement_series : []
  const hasMovements = hasStockMovement(movementSeries)
  const criticalItems = topStockCriticalItems(data.below_minimum)

  return <>
    <section className="report-metric-group" aria-labelledby="stock-metrics-title">
      <div className="report-section-heading">
        <div>
          <p className="eyebrow">Posição atual</p>
          <h2 id="stock-metrics-title">Estoque no depósito</h2>
          <p>As quantidades permanecem associadas à unidade de medida de cada produto e não são somadas entre unidades diferentes.</p>
        </div>
        <p className="report-section-context">{data.deposit.name}</p>
      </div>
      <div className="report-metric-layout">
        <article className="report-primary-metric">
          <span className="dashboard-card-label">Produtos com saldo</span>
          <strong className="report-primary-metric-value">{data.products_with_balance}</strong>
          <span className="dashboard-card-description">Produtos ativos com saldo diferente de zero.</span>
        </article>
        <div className="report-supporting-metrics">
          <Metric label="Produtos ativos" value={data.active_products} detail="Posição atual" />
          <Metric label="Abaixo do mínimo" value={data.below_minimum.length} detail="Exigem atenção" />
          <Metric label="Movimentações" value={data.movement_count_in_period} detail="Eventos no período" />
        </div>
      </div>
    </section>

    <section className="report-visual-analysis" aria-labelledby="stock-analysis-title">
      <div className="report-section-heading">
        <div>
          <p className="eyebrow">Leitura visual</p>
          <h2 id="stock-analysis-title">Como o estoque se movimentou</h2>
          <p>As séries contam eventos que aumentaram ou reduziram o saldo, preservando ajustes, inventários, devoluções e reversões conforme seu efeito oficial.</p>
        </div>
      </div>

      <ReportChartPanel
        id="stock-movement-trend"
        variant="primary"
        eyebrow="Análise principal"
        title="Movimentações ao longo do período"
        description="Contagem de registros de entrada e saída no depósito selecionado."
        summary={hasMovements ? <div className="report-chart-summary"><div><span>Entradas no saldo</span><strong>{data.movement_entries}</strong></div><div><span>Saídas do saldo</span><strong>{data.movement_exits}</strong></div></div> : null}
        meta={hasCurrentPeriod ? `Granularidade: ${granularityLabel(data.granularity)}` : undefined}
      >
        {!hasCurrentPeriod && loading ? <div className="report-chart-empty" role="status"><strong>Atualizando movimentações</strong><p>A posição atual permanece disponível enquanto o novo período é carregado.</p></div> : hasMovements ? <div className="report-chart" aria-label="Gráfico de barras com entradas e saídas de estoque ao longo do período"><BarChart
          xAxis={[{ scaleType: 'band', data: movementSeries.map((point) => point.bucket), tickLabelInterval: reportTickLabelInterval(movementSeries.length, data.granularity), tickLabelStyle: chartAxisTickLabelStyle, valueFormatter: (value: string) => formatBucketLabel(value, data.granularity) }]}
          yAxis={[{ width: 48, min: 0, tickMinStep: 1, tickLabelStyle: chartAxisTickLabelStyle, valueFormatter: (value: number) => quantity(value) }]}
          series={[
            { data: movementSeries.map((point) => point.entries), label: 'Entradas no saldo', color: 'var(--color-primary)', valueFormatter: (value: number | null) => `${Number(value)} registros` },
            { data: movementSeries.map((point) => point.exits), label: 'Saídas do saldo', color: 'var(--color-accent)', valueFormatter: (value: number | null) => `${Number(value)} registros` },
          ]}
          slotProps={{ tooltip: { trigger: 'axis' } }}
          height={300}
          margin={{ top: 36, right: 20, bottom: 34, left: 8 }}
          grid={{ horizontal: true }}
          sx={chartSx}
        /></div> : <ChartEmptyState title="Nenhuma movimentação no período selecionado" description="Escolha uma janela maior para investigar entradas e saídas anteriores." />}
      </ReportChartPanel>

      <div className="report-stock-attention">
        <ReportChartPanel
          id="stock-critical-ranking"
          variant="supporting"
          eyebrow="Atenção operacional"
          title="Produtos abaixo do mínimo"
          description="Top 6 pela porcentagem que falta para alcançar o mínimo configurado."
          meta="Posição atual"
        >
          {criticalItems.length ? <StockCriticalRanking items={criticalItems} /> : data.below_minimum.length ? <ChartEmptyState title="Itens críticos sem percentual comparável" description="Há saldo abaixo de mínimo zero; consulte a tabela para avaliar o déficit na unidade do produto." /> : <ChartEmptyState title="Estoque dentro do mínimo" description="Nenhum item ativo exige atenção neste momento." />}
        </ReportChartPanel>
      </div>
    </section>

    <section className="report-analysis-section" aria-labelledby="stock-detail-title">
      <div className="report-section-heading">
        <div>
          <p className="eyebrow">Evidência detalhada</p>
          <h2 id="stock-detail-title">Saldos por produto</h2>
          <p>Compare saldo atual, mínimo e déficit sem perder a unidade de medida de cada item.</p>
        </div>
      </div>
      {data.balances.length ? <StockBalancesTable items={data.balances} /> : <div className="data-card report-detail-empty"><p>Não há produtos ativos para detalhar neste depósito.</p></div>}
    </section>
  </>
}

function StockCriticalRanking({ items }: { items: ReturnType<typeof topStockCriticalItems> }) {
  const labels = items.map((item) => item.product_name)
  const values = items.map((item) => item.shortfall_percent ?? 0)
  const chartHeight = Math.max(176, items.length * 32 + 56)
  return <div className="report-chart" aria-label="Gráfico de barras com produtos abaixo do estoque mínimo"><BarChart
    layout="horizontal"
    xAxis={[{ min: 0, tickLabelStyle: chartAxisTickLabelStyle, valueFormatter: (value: number) => `${value.toFixed(0)}%` }]}
    yAxis={[{ scaleType: 'band', data: labels, tickLabelStyle: chartAxisTickLabelStyle, valueFormatter: (value: string, context) => context.location === 'tooltip' ? value : truncateRankingLabel(value, 24), width: 176 }]}
    series={[{ data: values, label: 'Déficit até o mínimo', color: 'var(--color-warning)', valueFormatter: (value: number | null) => `${Number(value).toFixed(1)}% abaixo do mínimo` }]}
    slotProps={{ tooltip: { trigger: 'axis' } }}
    hideLegend
    height={chartHeight}
    margin={{ top: 12, right: 36, bottom: 32, left: 8 }}
    grid={{ vertical: true }}
    sx={chartSx}
  /></div>
}

function StockBalancesTable({ items }: { items: StockReport['balances'] }) {
  return <div className="data-card data-table-wrap report-detail-table report-stock-table"><table className="data-table"><caption className="sr-only">Saldos atuais agrupados por produto</caption><thead><tr><th scope="col">Produto</th><th scope="col">Saldo atual</th><th scope="col">Mínimo</th><th scope="col">Déficit</th><th scope="col">Status</th></tr></thead><tbody>{items.map((item) => <tr key={item.produto_id}><td className="data-primary"><span>{item.product_name}</span><small>{item.sku}</small></td><td className="report-number-cell">{quantity(Number(item.saldo))} {item.unit}</td><td className="report-number-cell">{quantity(Number(item.estoque_minimo))} {item.unit}</td><td className="report-number-cell">{quantity(Number(item.deficit))} {item.unit}</td><td><span className={`report-stock-status${item.abaixo_do_minimo ? ' is-critical' : ''}`}>{item.abaixo_do_minimo ? 'Abaixo do mínimo' : 'Dentro do mínimo'}</span></td></tr>)}</tbody></table></div>
}

export function FinanceReportPage() {
  const [period, setPeriod] = useState<DashboardAnalyticsPeriod>('12m')
  const [data, setData] = useState<FinanceReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const load = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      setData(await getFinanceReport(period))
    } catch (cause) {
      setError(getApiErrorMessage(cause, 'Não foi possível carregar o relatório financeiro.'))
    } finally {
      setLoading(false)
    }
  }, [period])
  useEffect(() => { void load() }, [load])
  const rows = data ? [{ contas_a_receber: data.receivable_titles, contas_a_pagar: data.payable_titles, vencidos: data.overdue_installments, previsto_receber: data.previsto_receber, previsto_pagar: data.previsto_pagar }] : []
  const selectedPeriodLabel = dashboardPeriodOptions.find((option) => option.value === period)?.label ?? period
  const hasCurrentPeriod = data?.period === period
  const scopeDescription = hasCurrentPeriod
    ? `${selectedPeriodLabel}: ${formatDateRange(data.date_from, data.date_to)}`
    : `${selectedPeriodLabel}: atualizando recorte`

  return <div className="page-stack">
    <PageHeader eyebrow="Relatórios" title="Relatório financeiro" description="Posição financeira, compromissos por vencimento e valores que pedem atenção." pageId="reports_finance" />
    <div className="report-toolbar">
      <label className="dashboard-period-field">
        <span>Período dos vencimentos</span>
        <select value={period} onChange={(event) => setPeriod(event.target.value as DashboardAnalyticsPeriod)}>
          {dashboardPeriodOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
      </label>
      <ExportButton rows={rows} filename="relatorio-financeiro.csv" />
    </div>
    <div className="report-active-scope" aria-label={`Escopo analítico: ${scopeDescription}`}>
      <strong>Escopo analítico</strong>
      <span>{scopeDescription}</span>
      <span>Posição financeira: todo o histórico</span>
    </div>
    {error ? <ErrorState description={error} onRetry={() => void load()} /> : null}
    {!data && loading ? <LoadingState label="Carregando relatório financeiro..." /> : null}
    {!error && data ? <FinanceReportContent data={data} selectedPeriod={period} loading={loading} /> : null}
  </div>
}

function FinanceReportContent({ data, selectedPeriod, loading }: { data: FinanceReport; selectedPeriod: DashboardAnalyticsPeriod; loading: boolean }) {
  const hasCurrentPeriod = data.period === selectedPeriod
  const commitments = hasCurrentPeriod ? data.commitments : []
  const hasCommitments = hasPositiveValue(commitments.flatMap((point) => [point.receivable, point.payable]))
  const receivableInPeriod = commitments.reduce((total, point) => total + point.receivable, 0)
  const payableInPeriod = commitments.reduce((total, point) => total + point.payable, 0)
  const overdueTotal = data.overdue_receivable + data.overdue_payable

  return <>
    <section className="report-metric-group" aria-labelledby="finance-metrics-title">
      <div className="report-section-heading">
        <div>
          <p className="eyebrow">Posição financeira</p>
          <h2 id="finance-metrics-title">Saldos e liquidações</h2>
          <p>Os saldos em aberto descontam liquidações confirmadas; recebido e pago mostram o realizado acumulado.</p>
        </div>
        <p className="report-section-context">Todo o histórico</p>
      </div>
      <div className="report-metric-layout">
        <article className="report-primary-metric">
          <span className="dashboard-card-label">A receber em aberto</span>
          <strong className="report-primary-metric-value">{money(Number(data.previsto_receber))}</strong>
          <span className="dashboard-card-description">Saldo remanescente dos títulos a receber.</span>
        </article>
        <div className="report-supporting-metrics">
          <Metric label="A pagar em aberto" value={money(Number(data.previsto_pagar))} detail="Saldo remanescente" />
          <Metric label="Recebido" value={money(Number(data.realizado_receber))} detail="Liquidações confirmadas" />
          <Metric label="Pago" value={money(Number(data.realizado_pagar))} detail="Liquidações confirmadas" />
        </div>
      </div>
      <div className="report-finance-counts" aria-label="Quantidade de títulos financeiros">
        <span><strong>{data.receivable_titles}</strong> títulos a receber</span>
        <span><strong>{data.payable_titles}</strong> títulos a pagar</span>
      </div>
    </section>

    <section className="report-visual-analysis" aria-labelledby="finance-analysis-title">
      <div className="report-section-heading">
        <div>
          <p className="eyebrow">Leitura visual</p>
          <h2 id="finance-analysis-title">Quando os compromissos vencem</h2>
          <p>Compare entradas e saídas ainda em aberto pela data de vencimento das parcelas.</p>
        </div>
      </div>

      <ReportChartPanel
        id="finance-commitments"
        variant="primary"
        eyebrow="Análise principal"
        title="Compromissos por vencimento"
        description="Valores ainda em aberto no período selecionado, agrupados pela mesma unidade temporal."
        summary={hasCommitments ? <div className="report-chart-summary"><div><span>A receber no período</span><strong>{money(receivableInPeriod)}</strong></div><div><span>A pagar no período</span><strong>{money(payableInPeriod)}</strong></div></div> : null}
        meta={hasCurrentPeriod ? `Granularidade: ${granularityLabel(data.granularity)}` : undefined}
      >
        {!hasCurrentPeriod && loading ? <div className="report-chart-empty" role="status"><strong>Atualizando análise financeira</strong><p>Os indicadores de posição permanecem disponíveis enquanto o novo período é carregado.</p></div> : hasCommitments ? <div className="report-chart" aria-label="Gráfico de barras com valores a receber e a pagar em aberto por vencimento"><BarChart
          xAxis={[{ scaleType: 'band', data: commitments.map((point) => point.bucket), tickLabelInterval: reportTickLabelInterval(commitments.length, data.granularity), tickLabelStyle: chartAxisTickLabelStyle, valueFormatter: (value: string) => formatBucketLabel(value, data.granularity) }]}
          yAxis={[{ width: 72, tickLabelStyle: chartAxisTickLabelStyle, valueFormatter: (value: number) => formatCompactMoney(value) }]}
          series={[
            { data: commitments.map((point) => point.receivable), label: 'A receber em aberto', color: 'var(--color-primary)', valueFormatter: (value: number | null) => formatMoney(Number(value)) },
            { data: commitments.map((point) => point.payable), label: 'A pagar em aberto', color: 'var(--color-accent)', valueFormatter: (value: number | null) => formatMoney(Number(value)) },
          ]}
          slotProps={{ tooltip: { trigger: 'axis' } }}
          height={300}
          margin={{ top: 36, right: 20, bottom: 34, left: 8 }}
          grid={{ horizontal: true }}
          sx={chartSx}
        /></div> : <ChartEmptyState title="Nenhum compromisso em aberto neste período" description="Não há parcelas com saldo remanescente e vencimento dentro do recorte selecionado." />}
      </ReportChartPanel>

      <ReportChartPanel
        id="finance-overdue-attention"
        variant="supporting"
        eyebrow="Atenção atual"
        title="Parcelas vencidas ainda em aberto"
        description="Apenas parcelas com vencimento anterior a hoje e saldo remanescente positivo."
        meta="Todo o histórico"
      >
        {data.overdue_open_installments > 0 ? <div className="report-chart-summary report-finance-attention-summary"><div><span>Valor em atraso</span><strong>{money(overdueTotal)}</strong></div><div><span>Parcelas</span><strong>{data.overdue_open_installments}</strong></div><div><span>A receber</span><strong>{money(data.overdue_receivable)}</strong></div><div><span>A pagar</span><strong>{money(data.overdue_payable)}</strong></div></div> : <ChartEmptyState title="Nenhuma parcela vencida em aberto" description="Não há saldos remanescentes vencidos que exijam atenção neste momento." />}
      </ReportChartPanel>
    </section>
  </>
}

function ReportLayout({ pageId, loaded, eyebrow, title, description, filters, setFilters, onSubmit, rows, filename, error, onRetry, emptyTitle = 'Nenhum dado encontrado', emptyDescription = 'Não há registros para os filtros ou período selecionado.', children }: { pageId: string; loaded: boolean; eyebrow: string; title: string; description: string; filters?: ReportFilters; setFilters?: (filters: ReportFilters) => void; onSubmit?: () => void; rows: Array<Record<string, string | number>>; filename: string; error: string | null; onRetry: () => void; emptyTitle?: string; emptyDescription?: string; children: ReactNode }) {
  return <div className="page-stack"><PageHeader eyebrow={eyebrow} title={title} description={description} pageId={pageId} /><div className="report-toolbar"><div>{filters && setFilters && onSubmit ? <FilterBar filters={filters} onChange={setFilters} onSubmit={onSubmit} /> : null}</div><ExportButton rows={rows} filename={filename} /></div>{filters ? <div className="report-active-scope" aria-label={`Escopo ativo: ${formatPeriod(filters)}`}><strong>Escopo ativo</strong><span>{formatPeriod(filters)}</span></div> : null}{error ? <ErrorState description={error} onRetry={onRetry} /> : null}{!error && !loaded ? <LoadingState label="Carregando relatório..." /> : null}{!error && loaded && !rows.length ? <div className="data-card"><EmptyState title={emptyTitle} description={emptyDescription} /></div> : null}{!error && loaded && rows.length ? children : null}</div>
}
