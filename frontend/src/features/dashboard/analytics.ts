export type DashboardAnalyticsPeriod = '30d' | '90d' | '6m' | '12m'
export type DashboardAnalyticsGranularity = 'day' | 'week' | 'month'

export type DashboardAnalytics = {
  period: DashboardAnalyticsPeriod
  date_from: string
  date_to: string
  granularity: DashboardAnalyticsGranularity
  sales_trend: Array<{
    bucket: string
    sales_value: number
    completed_sales: number
  }>
  finance_trend: Array<{
    bucket: string
    receivable: number
    payable: number
  }>
  stock_attention: Array<{
    product_id: number
    product_name: string
    shortfall_percent: number
    saldo: number
    estoque_minimo: number
  }>
}

export const dashboardPeriodOptions: Array<{ value: DashboardAnalyticsPeriod; label: string }> = [
  { value: '30d', label: 'Últimos 30 dias' },
  { value: '90d', label: 'Últimas 12 semanas' },
  { value: '6m', label: 'Últimos 6 meses' },
  { value: '12m', label: 'Últimos 12 meses' },
]

export function getTickLabelInterval(pointCount: number, granularity: DashboardAnalyticsGranularity) {
  const step = pointCount <= 8 ? 1 : granularity === 'day' ? 5 : Math.ceil(pointCount / 5)
  return (_value: unknown, index: number) => index % step === 0 || index === pointCount - 1
}

function parseDate(value: string) {
  return new Date(`${value}T00:00:00`)
}

export function formatDate(value: string) {
  return new Intl.DateTimeFormat('pt-BR').format(parseDate(value))
}

export function formatDateRange(dateFrom: string, dateTo: string) {
  return `${formatDate(dateFrom)} a ${formatDate(dateTo)}`
}

export function formatBucketLabel(value: string, granularity: DashboardAnalyticsGranularity) {
  const date = parseDate(value)
  if (granularity === 'day') {
    return new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: '2-digit' }).format(date)
  }
  if (granularity === 'week') {
    return `Sem. ${new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: '2-digit' }).format(date)}`
  }
  const monthLabels = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
  return `${monthLabels[date.getMonth()]}/${String(date.getFullYear()).slice(-2)}`
}

export function formatMoney(value: number) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value || 0)
}

export function formatCompactMoney(value: number) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', notation: 'compact', maximumFractionDigits: 1 }).format(value || 0)
}

export function formatNumber(value: number) {
  return new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 3 }).format(value || 0)
}

export function hasPositiveValue(values: number[]) {
  return values.some((value) => value > 0)
}
