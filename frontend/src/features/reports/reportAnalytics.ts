import type { CommercialReport } from './api'

export const commercialChartTopN = 6

export function truncateRankingLabel(label: string, maxLength: number) {
  const normalized = label.trim()
  if (normalized.length <= maxLength) return normalized

  const visibleLength = Math.max(1, maxLength - 1)
  return `${normalized.slice(0, visibleLength).trimEnd()}…`
}

export function topProductContributors(items: CommercialReport['by_product']) {
  return [...items]
    .sort((left, right) => right.total - left.total || left.product_id - right.product_id)
    .slice(0, commercialChartTopN)
}

export function topCustomerContributors(items: CommercialReport['by_customer']) {
  return [...items]
    .sort((left, right) => right.total - left.total || (left.customer_id ?? 0) - (right.customer_id ?? 0))
    .slice(0, commercialChartTopN)
}

export function hasPositiveTrend(points: NonNullable<CommercialReport['sales_trend']>) {
  return points.some((point) => point.sales_value > 0)
}

export function sumTrendValue(points: NonNullable<CommercialReport['sales_trend']>) {
  return points.reduce((total, point) => total + point.sales_value, 0)
}

export function sumTrendSales(points: NonNullable<CommercialReport['sales_trend']>) {
  return points.reduce((total, point) => total + point.completed_sales, 0)
}
