import { appearanceLabels, defaultAppearance, type AppearanceLabels } from '../features/settings/types'
import { navigationIcons, type AppIcon } from './iconography'

export type NavigationItem = {
  path: string
  label: string
  icon: AppIcon
}

export type NavigationGroup = {
  label: string
  items: NavigationItem[]
  moduleCode?: string
  collapsible?: boolean
}

export type RouteDefinition = NavigationItem & {
  description: string
}

export function getNavigationGroups(
  labels: AppearanceLabels,
  activeModules?: ReadonlySet<string>,
  canManageUsers = true,
): NavigationGroup[] {
  const groups: NavigationGroup[] = [
    {
      label: 'Visão geral',
      items: [{ path: '/', label: labels.dashboard, icon: navigationIcons.dashboard }],
    },
    {
      label: 'Cadastros',
      items: [
        { path: '/customers', label: labels.customers, icon: navigationIcons.customers },
        { path: '/products', label: labels.products, icon: navigationIcons.products },
        { path: '/suppliers', label: labels.suppliers, icon: navigationIcons.suppliers },
        { path: '/employees', label: labels.employees, icon: navigationIcons.employees },
      ],
    },
    {
      label: 'Comercial',
      moduleCode: 'commercial',
      collapsible: true,
      items: [
        { path: '/sales/new', label: labels.newSale, icon: navigationIcons.newSale },
        { path: '/sales', label: labels.sales, icon: navigationIcons.sales },
        { path: '/commercial/quotes', label: 'Orçamentos', icon: navigationIcons.quotes },
        { path: '/commercial/orders', label: 'Pedidos de venda', icon: navigationIcons.orders },
        { path: '/commercial/returns', label: 'Devoluções', icon: navigationIcons.returns },
      ],
    },
    {
      label: 'Compras',
      moduleCode: 'purchases',
      items: [
        { path: '/purchases', label: 'Pedidos de compra', icon: navigationIcons.purchases },
        { path: '/purchases/receipts', label: 'Recebimentos', icon: navigationIcons.receipts },
      ],
    },
    {
      label: 'Estoque',
      moduleCode: 'inventory',
      collapsible: true,
      items: [
        { path: '/inventory/balances', label: 'Saldos', icon: navigationIcons.inventoryBalances },
        { path: '/inventory/movements', label: 'Movimentações', icon: navigationIcons.inventoryMovements },
        { path: '/inventory/adjustments', label: 'Ajustes', icon: navigationIcons.inventoryAdjustments },
        { path: '/inventory/inventories', label: 'Inventários', icon: navigationIcons.inventories },
        { path: '/inventory/deposits', label: 'Depósitos', icon: navigationIcons.deposits },
      ],
    },
    {
      label: 'Financeiro',
      moduleCode: 'finance',
      items: [
        { path: '/finance/receivables', label: 'Contas a receber', icon: navigationIcons.receivables },
        { path: '/finance/payables', label: 'Contas a pagar', icon: navigationIcons.payables },
        { path: '/finance/cashflow', label: 'Caixa e fluxo', icon: navigationIcons.cashflow },
      ],
    },
    {
      label: 'Relatórios',
      moduleCode: 'reports',
      collapsible: true,
      items: [
        { path: '/reports/commercial', label: 'Comercial', icon: navigationIcons.commercialReport },
        { path: '/reports/purchases', label: 'Compras', icon: navigationIcons.purchases },
        { path: '/reports/stock', label: 'Estoque', icon: navigationIcons.inventoryBalances },
        { path: '/reports/finance', label: 'Financeiro', icon: navigationIcons.financeReport },
      ],
    },
    {
      label: 'Configurações',
      items: [
        { path: '/settings', label: 'Visão geral', icon: navigationIcons.settings },
        { path: '/settings/appearance', label: 'Aparência', icon: navigationIcons.appearance },
        { path: '/settings/custom-fields', label: 'Campos personalizados', icon: navigationIcons.customFields },
        { path: '/settings/modules', label: 'Módulos', icon: navigationIcons.settings },
        ...(canManageUsers ? [{ path: '/settings/users', label: 'Usuários', icon: navigationIcons.users }] : []),
        { path: '/settings/payment-conditions', label: 'Condições de pagamento', icon: navigationIcons.paymentConditions },
      ],
    },
  ]
  return groups.filter((group) => !group.moduleCode || !activeModules || activeModules.has(group.moduleCode))
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
  '/reports/commercial': 'Analise vendas, cancelamentos e devoluções.',
  '/reports/purchases': 'Acompanhe pedidos e recebimentos pendentes.',
  '/reports/stock': 'Analise saldos e produtos abaixo do mínimo.',
  '/reports/finance': 'Analise títulos, vencimentos e fluxo financeiro.',
  '/settings/modules': 'Ative ou desative áreas disponíveis no ERP.',
  '/settings': 'Encontre as definições do ERP organizadas por finalidade.',
  '/settings/users': 'Administre acessos, papéis e vínculos com a equipe.',
  '/settings/appearance': 'Personalize a identidade visual e os rótulos do sistema.',
  '/settings/custom-fields': 'Defina campos extras para os cadastros operacionais.',
  '/settings/payment-conditions': 'Gerencie as condições de pagamento comerciais.',
}

export function getModuleForPath(pathname: string): string | null {
  if (pathname.startsWith('/commercial') || pathname.startsWith('/sales')) return 'commercial'
  if (pathname.startsWith('/purchases')) return 'purchases'
  if (pathname.startsWith('/inventory')) return 'inventory'
  if (pathname.startsWith('/finance')) return 'finance'
  if (pathname.startsWith('/reports')) return 'reports'
  return null
}

export const notFoundRoute: RouteDefinition = {
  path: '/not-found',
  label: 'Página não encontrada',
  icon: navigationIcons.alert,
  description: 'A página que você tentou acessar não existe.',
}

const legacyRouteRedirects: Record<string, string> = {
  '/reports/dashboard': '/',
}

export function getCanonicalPathname(pathname: string): string {
  const normalizedPath = pathname.replace(/\/$/, '') || '/'
  return legacyRouteRedirects[normalizedPath] ?? normalizedPath
}

export function getRoute(
  pathname: string,
  labels = appearanceLabels(defaultAppearance),
): RouteDefinition {
  const normalizedPath = getCanonicalPathname(pathname)
  const routeItems = getNavigationGroups(labels).flatMap((group) => group.items)
  const item = routeItems.find((candidate) => candidate.path === normalizedPath)

  if (!item) return notFoundRoute

  return {
    ...item,
    description: routeDescriptions[item.path],
  }
}
