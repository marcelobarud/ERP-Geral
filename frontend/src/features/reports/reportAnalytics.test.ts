import { describe, expect, it } from 'vitest'

import {
  hasPositiveTrend,
  hasStockMovement,
  sumTrendSales,
  sumTrendValue,
  topCustomerContributors,
  topProductContributors,
  topStockCriticalItems,
  truncateRankingLabel,
} from './reportAnalytics'

describe('commercial report analytics helpers', () => {
  it('orders product contributions by value and keeps only the top six', () => {
    const items = Array.from({ length: 7 }, (_, index) => ({
      product_id: index + 1,
      product_name: `Produto ${index + 1}`,
      quantity: 1,
      total: index + 1,
    }))

    expect(topProductContributors(items).map((item) => item.product_id)).toEqual([7, 6, 5, 4, 3, 2])
  })

  it('orders customer contributions by value, resolves ties by id and keeps six items', () => {
    const items = Array.from({ length: 7 }, (_, index) => ({
      customer_id: index + 1,
      customer_name: `Cliente ${index + 1}`,
      sales: 1,
      total: index === 0 ? 20 : index === 1 ? 20 : index + 1,
    }))

    expect(topCustomerContributors(items).map((item) => item.customer_id)).toEqual([1, 2, 7, 6, 5, 4])
  })

  it('truncates only the visible ranking label while preserving a readable suffix', () => {
    expect(truncateRankingLabel('Cliente Demonstração com nome muito longo', 24)).toBe('Cliente Demonstração co…')
    expect(truncateRankingLabel('Produto curto', 24)).toBe('Produto curto')
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

describe('stock report analytics helpers', () => {
  it('keeps the six greatest comparable critical percentages', () => {
    const items = [
      ...Array.from({ length: 7 }, (_, index) => ({
        produto_id: index + 1,
        deposito_id: 1,
        saldo: 1,
        estoque_minimo: 10,
        abaixo_do_minimo: true,
        product_name: `Produto ${index + 1}`,
        sku: `SKU-${index + 1}`,
        unit: 'UN',
        deficit: 9,
        shortfall_percent: index + 1,
      })),
      {
        produto_id: 99,
        deposito_id: 1,
        saldo: -1,
        estoque_minimo: 0,
        abaixo_do_minimo: true,
        product_name: 'Mínimo zero',
        sku: 'ZERO',
        unit: 'UN',
        deficit: 1,
        shortfall_percent: null,
      },
    ]

    expect(topStockCriticalItems(items).map((item) => item.produto_id)).toEqual([7, 6, 5, 4, 3, 2])
  })

  it('recognizes sparse series with only entries or only exits', () => {
    expect(hasStockMovement([{ bucket: '2026-09-01', entries: 1, exits: 0 }])).toBe(true)
    expect(hasStockMovement([{ bucket: '2026-09-01', entries: 0, exits: 1 }])).toBe(true)
    expect(hasStockMovement([{ bucket: '2026-09-01', entries: 0, exits: 0 }])).toBe(false)
  })
})
