import { describe, expect, it } from 'vitest'

import { getNavigationGroups, getRoute } from './routes'
import { appearanceLabels, defaultAppearance } from '../features/settings/types'

describe('navegação comercial', () => {
  it('expõe os quatro fluxos comerciais e as condições de pagamento', () => {
    const groups = getNavigationGroups(appearanceLabels(defaultAppearance))
    const commercial = groups.find((group) => group.label === 'Comercial')

    expect(commercial?.collapsible).toBe(true)
    expect(groups.find((group) => group.label === 'Estoque')?.collapsible).toBe(true)
    expect(groups.find((group) => group.label === 'Relatórios')?.collapsible).toBe(true)
    expect(groups.find((group) => group.label === 'Compras')?.collapsible).toBeUndefined()

    expect(commercial?.items.map((item) => item.path)).toEqual([
      '/sales/new',
      '/sales',
      '/commercial/quotes',
      '/commercial/orders',
      '/commercial/returns',
    ])
    expect(groups.find((group) => group.label === 'Vendas')).toBeUndefined()
    expect(groups.flatMap((group) => group.items).map((item) => item.path)).toContain(
      '/settings/payment-conditions',
    )
    expect(groups.find((group) => group.label === 'Compras')?.items.map((item) => item.path)).toEqual([
      '/purchases',
      '/purchases/receipts',
    ])
    expect(groups.find((group) => group.label === 'Estoque')?.items.map((item) => item.path)).toEqual([
      '/inventory/balances',
      '/inventory/movements',
      '/inventory/adjustments',
      '/inventory/inventories',
      '/inventory/deposits',
    ])
    expect(groups.find((group) => group.label === 'Financeiro')?.items.map((item) => item.path)).toEqual([
      '/finance/receivables',
      '/finance/payables',
      '/finance/cashflow',
    ])
    expect(groups.find((group) => group.label === 'Relatórios')?.items.map((item) => item.path)).toEqual([
      '/reports/dashboard',
      '/reports/commercial',
      '/reports/purchases',
      '/reports/stock',
      '/reports/finance',
    ])
    expect(groups.find((group) => group.label === 'Configurações')?.items.map((item) => item.path)).toContain('/settings/modules')
    const onlyFinance = getNavigationGroups(appearanceLabels(defaultAppearance), new Set(['finance']))
    expect(onlyFinance.find((group) => group.label === 'Financeiro')).toBeTruthy()
    expect(onlyFinance.find((group) => group.label === 'Estoque')).toBeUndefined()
  })

  it('resolve as rotas comerciais com descrição própria', () => {
    expect(getRoute('/commercial/quotes').label).toBe('Orçamentos')
    expect(getRoute('/commercial/orders').label).toBe('Pedidos de venda')
    expect(getRoute('/commercial/returns').description).toContain('devoluções')
    expect(getRoute('/purchases/receipts').label).toBe('Recebimentos')
    expect(getRoute('/inventory/balances').label).toBe('Saldos')
    expect(getRoute('/finance/receivables').label).toBe('Contas a receber')
    expect(getRoute('/reports/dashboard').label).toBe('Dashboard ERP')
  })
})
