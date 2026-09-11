import { appearanceLabels, defaultAppearance, type AppearanceLabels } from '../features/settings/types'

export type NavigationItem = {
  path: string
  label: string
  icon: string
}

export type NavigationGroup = {
  label: string
  items: NavigationItem[]
}

export type RouteDefinition = NavigationItem & {
  description: string
}

export function getNavigationGroups(labels: AppearanceLabels): NavigationGroup[] {
  return [
    {
      label: 'Visão geral',
      items: [{ path: '/', label: labels.dashboard, icon: '⌂' }],
    },
    {
      label: 'Cadastros',
      items: [
        { path: '/customers', label: labels.customers, icon: '◎' },
        { path: '/products', label: labels.products, icon: '▦' },
        { path: '/suppliers', label: labels.suppliers, icon: '◈' },
        { path: '/employees', label: labels.employees, icon: '♙' },
      ],
    },
    {
      label: 'Vendas',
      items: [
        { path: '/sales/new', label: labels.newSale, icon: '+' },
        { path: '/sales', label: labels.sales, icon: '↗' },
      ],
    },
    {
      label: 'Comercial',
      items: [
        { path: '/commercial/quotes', label: 'Orçamentos', icon: '▤' },
        { path: '/commercial/orders', label: 'Pedidos', icon: '▥' },
        { path: '/commercial/sales', label: 'Vendas comerciais', icon: '↗' },
        { path: '/commercial/returns', label: 'Devoluções', icon: '↩' },
      ],
    },
    {
      label: 'Compras',
      items: [
        { path: '/purchases', label: 'Pedidos', icon: '▧' },
        { path: '/purchases/receipts', label: 'Recebimentos', icon: '⇩' },
      ],
    },
    {
      label: 'Estoque',
      items: [
        { path: '/inventory/balances', label: 'Saldos', icon: '▦' },
        { path: '/inventory/movements', label: 'Movimentações', icon: '⇄' },
        { path: '/inventory/adjustments', label: 'Ajustes', icon: '±' },
        { path: '/inventory/inventories', label: 'Inventários', icon: '☷' },
        { path: '/inventory/deposits', label: 'Depósitos', icon: '⌂' },
      ],
    },
    {
      label: 'Financeiro',
      items: [
        { path: '/finance/receivables', label: 'Contas a receber', icon: '↗' },
        { path: '/finance/payables', label: 'Contas a pagar', icon: '↙' },
        { path: '/finance/cashflow', label: 'Caixa e fluxo', icon: '◫' },
      ],
    },
    {
      label: 'Configurações',
      items: [
        { path: '/settings/appearance', label: 'Aparência', icon: '◌' },
        { path: '/settings/custom-fields', label: 'Campos personalizados', icon: '✦' },
        { path: '/settings/payment-conditions', label: 'Condições de pagamento', icon: '◫' },
      ],
    },
  ]
}

export const navigationGroups = getNavigationGroups(appearanceLabels(defaultAppearance))

const routeDescriptions: Record<string, string> = {
  '/': 'Uma visão tranquila para acompanhar o dia e acessar suas principais áreas.',
  '/customers': 'A base para organizar seus clientes estará disponível aqui.',
  '/products': 'O catálogo de produtos do seu negócio ficará centralizado aqui.',
  '/suppliers': 'Seus fornecedores poderão ser acompanhados nesta área.',
  '/employees': 'A equipe responsável pela operação será organizada aqui.',
  '/sales/new': 'Registre uma venda com múltiplos itens e preços históricos.',
  '/sales': 'Consulte o histórico de vendas e seus totais.',
  '/commercial/quotes': 'Crie e acompanhe orçamentos comerciais.',
  '/commercial/orders': 'Gerencie pedidos de venda e conversões.',
  '/commercial/sales': 'Acesse as vendas originadas do fluxo comercial.',
  '/commercial/returns': 'Registre e aprove devoluções de vendas.',
  '/purchases': 'Gerencie pedidos de compra e itens pendentes.',
  '/purchases/receipts': 'Registre recebimentos parciais ou totais.',
  '/inventory/balances': 'Consulte saldos e níveis mínimos por depósito.',
  '/inventory/movements': 'Consulte as movimentações de estoque.',
  '/inventory/adjustments': 'Registre ajustes manuais com motivo.',
  '/inventory/inventories': 'Faça contagens e confirme inventários.',
  '/inventory/deposits': 'Gerencie depósitos e o depósito padrão.',
  '/finance/receivables': 'Acompanhe contas a receber e liquidações.',
  '/finance/payables': 'Acompanhe contas a pagar e liquidações.',
  '/finance/cashflow': 'Consulte o fluxo previsto e realizado.',
  '/settings/appearance': 'Personalize a identidade visual e os rótulos do sistema.',
  '/settings/custom-fields': 'Defina campos extras para os cadastros operacionais.',
  '/settings/payment-conditions': 'Gerencie as condições de pagamento comerciais.',
}

export const notFoundRoute: RouteDefinition = {
  path: '/not-found',
  label: 'Página não encontrada',
  icon: '?',
  description: 'A página que você tentou acessar não existe.',
}

export function getRoute(
  pathname: string,
  labels = appearanceLabels(defaultAppearance),
): RouteDefinition {
  const normalizedPath = pathname.replace(/\/$/, '') || '/'
  const routeItems = getNavigationGroups(labels).flatMap((group) => group.items)
  const item = routeItems.find((candidate) => candidate.path === normalizedPath)

  if (!item) return notFoundRoute

  return {
    ...item,
    description: routeDescriptions[item.path],
  }
}
