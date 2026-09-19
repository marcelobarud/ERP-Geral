import type { ReactNode } from 'react'

import { BarChart } from '@mui/x-charts/BarChart'
import { LineChart } from '@mui/x-charts/LineChart'

import { actionIcons, iconSizes, iconStroke } from '../../app/iconography'
import { EmptyState } from '../../components/EmptyState'
import { ErrorState } from '../../components/ErrorState'
import { LoadingState } from '../../components/LoadingState'
import { useCustomizable } from '../settings/VisualCustomizationContext'
import {
  dashboardPeriodOptions,
  chartAxisTickLabelStyle,
  chartSx,
  formatBucketLabel,
  formatCompactMoney,
  formatDateRange,
  formatMoney,
  getTickLabelInterval,
  hasPositiveValue,
  type DashboardAnalytics,
  type DashboardAnalyticsPeriod,
} from './analytics'

const ArrowRightIcon = actionIcons.arrowRight

const dashboardChartHeights = {
  primary: 232,
  supporting: 172,
  stock: 172,
} as const

type DashboardChartPanelProps = {
  id: string
  variant: 'primary' | 'supporting'
  eyebrow: string
  title: string
  description: string
  href: string
  linkLabel: string
  onNavigate: (path: string) => void
  loading: boolean
  error: string | null
  onRetry: () => void
  summary?: ReactNode
  emptyTitle?: string
  emptyDescription?: string
  children?: ReactNode
}

function DashboardChartPanel({
  id,
  variant,
  eyebrow,
  title,
  description,
  href,
  linkLabel,
  onNavigate,
  loading,
  error,
  onRetry,
  summary,
  emptyTitle,
  emptyDescription,
  children,
}: DashboardChartPanelProps) {
  const surfaceCustomization = useCustomizable({
    key: `dashboard.analytics.${id}.panel`,
    type: 'SURFACE',
    group: 'analytics-panel',
    page: 'dashboard',
    label: title,
  })
  const hasChart = Boolean(children)

  return (
    <section className={`dashboard-chart-panel dashboard-chart-panel-${id} dashboard-chart-panel-${variant}`} aria-labelledby={`${id}-title`} {...surfaceCustomization}>
      <div className="dashboard-chart-panel-header">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h3 id={`${id}-title`}>{title}</h3>
          <p>{description}</p>
        </div>
        <a className="dashboard-chart-link" href={href} onClick={(event) => { event.preventDefault(); onNavigate(href) }}>
          {linkLabel}
          <ArrowRightIcon size={iconSizes.action} stroke={iconStroke} aria-hidden="true" focusable="false" />
        </a>
      </div>
      <div className="dashboard-chart-panel-body" aria-busy={loading}>
        {loading && !hasChart ? <LoadingState label="Carregando análise..." /> : null}
        {error ? <ErrorState description={error} onRetry={onRetry} /> : null}
        {!loading && !error && !hasChart && emptyTitle && emptyDescription ? <EmptyState title={emptyTitle} description={emptyDescription} /> : null}
        {loading && hasChart ? <p className="dashboard-chart-refresh" role="status">Atualizando análise...</p> : null}
        {summary}
        {children}
      </div>
    </section>
  )
}

type DashboardAnalyticsProps = {
  data: DashboardAnalytics | null
  period: DashboardAnalyticsPeriod
  loading: boolean
  error: string | null
  onPeriodChange: (period: DashboardAnalyticsPeriod) => void
  onRetry: () => void
  onNavigate: (path: string) => void
}

export function DashboardAnalytics({ data, period, loading, error, onPeriodChange, onRetry, onNavigate }: DashboardAnalyticsProps) {
  const currentData = data?.period === period ? data : null
  const salesPoints = currentData?.sales_trend ?? []
  const financePoints = currentData?.finance_trend ?? []
  const stockAttention = currentData?.stock_attention ?? []
  const hasSales = hasPositiveValue(salesPoints.map((point) => point.sales_value))
  const hasFinance = hasPositiveValue(financePoints.flatMap((point) => [point.receivable, point.payable]))
  const hasStockAttention = stockAttention.length > 0
  const totalSales = salesPoints.reduce((total, point) => total + point.sales_value, 0)
  const completedSales = salesPoints.reduce((total, point) => total + point.completed_sales, 0)
  const totalReceivable = financePoints.reduce((total, point) => total + point.receivable, 0)
  const totalPayable = financePoints.reduce((total, point) => total + point.payable, 0)

  return (
    <section className="dashboard-section dashboard-analytics" aria-labelledby="dashboard-analytics-title">
      <div className="dashboard-section-heading dashboard-analytics-heading">
        <div>
          <p className="eyebrow">Leitura analítica</p>
          <h2 id="dashboard-analytics-title">Desempenho recente</h2>
          <p className="dashboard-analytics-description">Tendências agregadas para entender o ritmo da operação e escolher onde investigar.</p>
        </div>
        <div className="dashboard-analytics-controls">
          <label className="dashboard-period-field" htmlFor="dashboard-analytics-period">
            <span>Período da análise</span>
            <select id="dashboard-analytics-period" value={period} onChange={(event) => onPeriodChange(event.target.value as DashboardAnalyticsPeriod)}>
              {dashboardPeriodOptions.map((option) => <option value={option.value} key={option.value}>{option.label}</option>)}
            </select>
          </label>
          <span className="dashboard-analytics-note">Afeta apenas as visualizações analíticas.</span>
        </div>
      </div>
      {currentData ? <div className="dashboard-analytics-scope" aria-live="polite"><strong>Escopo:</strong> {formatDateRange(currentData.date_from, currentData.date_to)} <span>· granularidade {currentData.granularity === 'day' ? 'diária' : currentData.granularity === 'week' ? 'semanal' : 'mensal'}</span></div> : null}
      <div className="dashboard-analytics-grid">
        <DashboardChartPanel
          id="dashboard-sales-trend"
          variant="primary"
          eyebrow="Atividade comercial"
          title="Vendas ao longo do tempo"
          description="Valor das vendas concluídas em cada intervalo do período selecionado."
          href="/reports/commercial"
          linkLabel="Abrir relatório comercial"
          onNavigate={onNavigate}
          loading={loading}
          error={error}
          onRetry={onRetry}
          summary={currentData && hasSales ? <div className="dashboard-chart-summary">
            <div className="dashboard-chart-summary-item">
              <span className="dashboard-chart-summary-label">Total vendido</span>
              <strong className="dashboard-chart-summary-value">{formatMoney(totalSales)}</strong>
              <span className="dashboard-chart-summary-context">{completedSales} {completedSales === 1 ? 'venda concluída' : 'vendas concluídas'} no período</span>
            </div>
          </div> : null}
          emptyTitle="Nenhuma venda no período"
          emptyDescription="Escolha uma janela maior para investigar outra tendência comercial."
        >
          {currentData && hasSales ? <div className="dashboard-chart" aria-label="Gráfico de linha com a evolução do valor das vendas concluídas"><LineChart
            xAxis={[{ data: salesPoints.map((point) => point.bucket), scaleType: 'point', tickLabelInterval: getTickLabelInterval(salesPoints.length, currentData.granularity), tickLabelStyle: chartAxisTickLabelStyle, valueFormatter: (value: string) => formatBucketLabel(value, currentData.granularity) }]}
            yAxis={[{ width: 64, tickLabelStyle: chartAxisTickLabelStyle, valueFormatter: (value: number) => formatCompactMoney(value) }]}
            series={[{ data: salesPoints.map((point) => point.sales_value), label: 'Vendas concluídas', color: 'var(--color-primary)', valueFormatter: (value: number | null) => formatMoney(Number(value)) }]}
            hideLegend
            height={dashboardChartHeights.primary}
            margin={{ top: 18, right: 18, bottom: 32, left: 8 }}
            grid={{ horizontal: true }}
            sx={chartSx}
          /></div> : null}
        </DashboardChartPanel>

        <DashboardChartPanel
          id="dashboard-finance-trend"
          variant="supporting"
          eyebrow="Situação financeira"
          title="Compromissos por vencimento"
          description="Valores ainda em aberto, separados entre receber e pagar."
          href="/finance/cashflow"
          linkLabel="Ver fluxo financeiro"
          onNavigate={onNavigate}
          loading={loading}
          error={error}
          onRetry={onRetry}
          summary={currentData && hasFinance ? <div className="dashboard-chart-summary dashboard-finance-summary">
            <div className="dashboard-chart-summary-item">
              <span className="dashboard-chart-summary-label">A receber</span>
              <strong className="dashboard-chart-summary-value">{formatMoney(totalReceivable)}</strong>
              <span className="dashboard-chart-summary-context">Em aberto no período</span>
            </div>
            <div className="dashboard-chart-summary-item">
              <span className="dashboard-chart-summary-label">A pagar</span>
              <strong className="dashboard-chart-summary-value">{formatMoney(totalPayable)}</strong>
              <span className="dashboard-chart-summary-context">Em aberto no período</span>
            </div>
          </div> : null}
          emptyTitle="Nenhum compromisso no período"
          emptyDescription="Não há parcelas financeiras em aberto nesta janela de análise."
        >
          {currentData && hasFinance ? <div className="dashboard-chart" aria-label="Gráfico de barras com compromissos financeiros em aberto"><BarChart
            xAxis={[{ data: financePoints.map((point) => point.bucket), scaleType: 'band', tickLabelInterval: getTickLabelInterval(financePoints.length, currentData.granularity), tickLabelStyle: chartAxisTickLabelStyle, valueFormatter: (value: string) => formatBucketLabel(value, currentData.granularity) }]}
            yAxis={[{ width: 64, tickLabelStyle: chartAxisTickLabelStyle, valueFormatter: (value: number) => formatCompactMoney(value) }]}
            series={[
              { data: financePoints.map((point) => point.receivable), label: 'A receber em aberto', color: 'var(--color-primary)', valueFormatter: (value: number | null) => formatMoney(Number(value)) },
              { data: financePoints.map((point) => point.payable), label: 'A pagar em aberto', color: 'var(--color-accent)', valueFormatter: (value: number | null) => formatMoney(Number(value)) },
            ]}
            height={dashboardChartHeights.supporting}
            margin={{ top: 18, right: 18, bottom: 32, left: 8 }}
            grid={{ horizontal: true }}
            sx={chartSx}
          /></div> : null}
        </DashboardChartPanel>

        <DashboardChartPanel
          id="dashboard-stock-attention"
          variant="supporting"
          eyebrow="Atenção operacional"
          title="Estoque abaixo do mínimo"
          description="Ranking dos itens pela porcentagem que falta para alcançar o mínimo configurado."
          href="/inventory/balances"
          linkLabel="Ver saldos"
          onNavigate={onNavigate}
          loading={loading}
          error={error}
          onRetry={onRetry}
          emptyTitle="Estoque dentro do mínimo"
          emptyDescription="Nenhum item ativo exige atenção neste momento."
        >
          {currentData && hasStockAttention ? <div className="dashboard-chart" aria-label="Gráfico de barras com produtos abaixo do estoque mínimo"><BarChart
            layout="horizontal"
            xAxis={[{ min: 0, max: 100, tickLabelStyle: chartAxisTickLabelStyle, valueFormatter: (value: number) => `${value.toFixed(0)}%` }]}
            yAxis={[{ scaleType: 'band', data: stockAttention.map((item) => item.product_name), tickLabelStyle: chartAxisTickLabelStyle, width: 120 }]}
            series={[{ data: stockAttention.map((item) => item.shortfall_percent), label: 'Déficit até o mínimo', color: 'var(--color-warning)', valueFormatter: (value: number | null) => `${Number(value).toFixed(1)}% abaixo do mínimo` }]}
            height={dashboardChartHeights.stock}
            margin={{ top: 18, right: 18, bottom: 32, left: 8 }}
            grid={{ vertical: true }}
            sx={chartSx}
          /></div> : null}
        </DashboardChartPanel>
      </div>
    </section>
  )
}
