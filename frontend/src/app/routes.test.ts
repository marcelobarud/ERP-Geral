import { describe, expect, it } from 'vitest'

import { getNavigationGroups, getRoute } from './routes'
import { appearanceLabels, defaultAppearance } from '../features/settings/types'

describe('navegação comercial', () => {
  it('expõe os quatro fluxos comerciais e as condições de pagamento', () => {
    const groups = getNavigationGroups(appearanceLabels(defaultAppearance))
    const commercial = groups.find((group) => group.label === 'Comercial')

    expect(commercial?.items.map((item) => item.path)).toEqual([
      '/commercial/quotes',
      '/commercial/orders',
      '/commercial/sales',
      '/commercial/returns',
    ])
    expect(groups.flatMap((group) => group.items).map((item) => item.path)).toContain(
      '/settings/payment-conditions',
    )
    expect(groups.find((group) => group.label === 'Compras')?.items.map((item) => item.path)).toEqual([
      '/purchases',
      '/purchases/receipts',
    ])
  })

  it('resolve as rotas comerciais com descrição própria', () => {
    expect(getRoute('/commercial/quotes').label).toBe('Orçamentos')
    expect(getRoute('/commercial/orders').label).toBe('Pedidos')
    expect(getRoute('/commercial/returns').description).toContain('devoluções')
    expect(getRoute('/purchases/receipts').label).toBe('Recebimentos')
  })
})
