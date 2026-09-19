import { describe, expect, it } from 'vitest'

import {
  hasPositiveTrend,
  sumTrendSales,
  sumTrendValue,
  topProductContributors,
} from './reportAnalytics'

describe('commercial report analytics helpers', () => {
  it('orders product contributions by value and keeps only the top eight', () => {
    const items = Array.from({ length: 9 }, (_, index) => ({
      product_id: index + 1,
      product_name: `Produto ${index + 1}`,
      quantity: 1,
      total: index + 1,
    }))

    expect(topProductContributors(items).map((item) => item.product_id)).toEqual([9, 8, 7, 6, 5, 4, 3, 2])
  })

  it('identifies and summarizes real temporal values', () => {
    const trend = [
      { bucket: '2026-08-01', sales_value: 0, completed_sales: 0 },
      { bucket: '2026-09-01', sales_value: 125.5, completed_sales: 2 },
    ]

    expect(hasPositiveTrend(trend)).toBe(true)
    expect(sumTrendValue(trend)).toBe(125.5)
    expect(sumTrendSales(trend)).toBe(2)
    expect(hasPositiveTrend([trend[0]])).toBe(false)
  })
})
