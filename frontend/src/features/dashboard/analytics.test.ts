import { describe, expect, it } from 'vitest'

import {
  formatBucketLabel,
  formatDateRange,
  formatMoney,
  getTickLabelInterval,
  hasPositiveValue,
} from './analytics'

describe('dashboard analytics formatting', () => {
  it('formats buckets according to the backend granularity', () => {
    expect(formatBucketLabel('2026-03-01', 'month')).toBe('mar/26')
    expect(formatBucketLabel('2026-03-09', 'week')).toBe('Sem. 09/03')
    expect(formatBucketLabel('2026-03-09', 'day')).toBe('09/03')
  })

  it('keeps the analytical scope and monetary formatting in Brazilian Portuguese', () => {
    expect(formatDateRange('2026-03-01', '2026-03-31')).toBe('01/03/2026 a 31/03/2026')
    expect(formatMoney(1234.5)).toContain('1.234,50')
  })

  it('identifies whether a chart has real positive data', () => {
    expect(hasPositiveValue([0, 0, 0])).toBe(false)
    expect(hasPositiveValue([0, 80, 0])).toBe(true)
  })

  it('reduces tick labels without dropping data points', () => {
    const interval = getTickLabelInterval(12, 'month')

    expect(interval('2026-01-01', 0)).toBe(true)
    expect(interval('2026-02-01', 1)).toBe(false)
    expect(interval('2026-12-01', 11)).toBe(true)
  })
})
