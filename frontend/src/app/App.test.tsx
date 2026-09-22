// @vitest-environment jsdom

import type { ReactNode } from 'react'
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as modulesApi from '../features/settings/modulesApi'

const { cadastrosReady, resolveCadastros, reportsReady, resolveReports } = vi.hoisted(() => {
  let resolveCadastrosImport: (() => void) | undefined
  const cadastros = new Promise<void>((nextResolve) => { resolveCadastrosImport = nextResolve })
  let resolve: (() => void) | undefined
  const ready = new Promise<void>((nextResolve) => { resolve = nextResolve })
  return { cadastrosReady: cadastros, resolveCadastros: () => resolveCadastrosImport?.(), reportsReady: ready, resolveReports: () => resolve?.() }
})

vi.mock('../components/AppLayout', () => ({
  AppLayout: ({ children }: { children: ReactNode }) => <div data-testid="app-shell">{children}</div>,
}))

vi.mock('../features/auth/AuthContext', () => ({
  AuthProvider: ({ children }: { children: ReactNode }) => <>{children}</>,
  useAuth: () => ({ authRequired: false, bootstrapAvailable: false, loading: false, user: null }),
}))

vi.mock('../features/settings/AppearanceContext', () => ({
  AppearanceProvider: ({ children }: { children: ReactNode }) => <>{children}</>,
  useAppearance: () => ({ preview: {}, pageAppearances: {}, loadPageAppearance: vi.fn() }),
}))

vi.mock('../features/settings/VisualCustomizationContext', () => ({
  VisualCustomizationProvider: ({ children }: { children: ReactNode }) => <>{children}</>,
  useCustomizable: () => ({}),
}))

vi.mock('../features/settings/modulesApi', () => ({ listModules: vi.fn().mockResolvedValue([]) }))

vi.mock('../features/dashboard/DashboardPage', () => ({ DashboardPage: () => <div>Dashboard imediato</div> }))
vi.mock('../features/cadastros/CadastrosRoutePages', async () => {
  await cadastrosReady
  return {
    CustomersPage: () => <div>Clientes lazy</div>,
    EmployeesPage: () => <div>Funcionários lazy</div>,
    ProductsPage: () => <div>Produtos lazy</div>,
    SuppliersPage: () => <div>Fornecedores lazy</div>,
  }
})
vi.mock('../features/sales/SalesPages', () => ({ NewSalePage: () => <div>Nova venda lazy</div>, SalesPage: () => <div>Vendas lazy</div> }))
vi.mock('../features/commercial/CommercialPages', () => ({ OrdersPage: () => <div>Pedidos lazy</div>, QuotesPage: () => <div>Orçamentos lazy</div>, ReturnsPage: () => <div>Devoluções lazy</div> }))
vi.mock('../features/purchases/PurchasesPages', () => ({ PurchasesPage: () => <div>Compras</div>, ReceiptsPage: () => <div>Recebimentos</div> }))
vi.mock('../features/inventory/InventoryPages', () => ({ AdjustmentsPage: () => <div>Ajustes lazy</div>, BalancesPage: () => <div>Saldos lazy</div>, DepositsPage: () => <div>Depósitos lazy</div>, InventoriesPage: () => <div>Inventários lazy</div>, MovementsPage: () => <div>Movimentações lazy</div> }))
vi.mock('../features/finance/FinancePages', () => ({ CashflowPage: () => <div>Caixa lazy</div>, FinancialTitlesPage: () => <div>Títulos lazy</div> }))
vi.mock('../features/auth/LoginPage', () => ({ LoginPage: () => <div>Login</div> }))
vi.mock('../features/auth/SetupPage', () => ({ SetupPage: () => <div>Setup</div> }))
vi.mock('../pages/NotFoundPage', () => ({ ModuleDisabledPage: () => <div>Módulo desativado</div>, NotFoundPage: () => <div>Não encontrado</div> }))

vi.mock('../features/reports/ReportsPages', async () => {
  await reportsReady
  return {
    CommercialReportPage: () => <div>Relatório comercial lazy</div>,
    FinanceReportPage: () => <div>Relatório financeiro lazy</div>,
    PurchasesReportPage: () => <div>Relatório de compras lazy</div>,
    StockReportPage: () => <div>Relatório de estoque lazy</div>,
  }
})

vi.mock('../features/settings/SettingsRoutePages', () => ({
  AppearancePage: () => <div>Aparência lazy</div>,
  CustomFieldsPage: () => <div>Campos personalizados lazy</div>,
  ModulesPage: () => <div>Módulos lazy</div>,
  PaymentConditionsPage: () => <div>Condições de pagamento lazy</div>,
  SettingsHubPage: () => <div>Configurações lazy</div>,
  UsersPage: () => <div>Usuários lazy</div>,
}))

import App from './App'

function visit(pathname: string) {
  window.history.replaceState({}, '', pathname)
  return render(<App />)
}

afterEach(() => {
  cleanup()
  window.history.replaceState({}, '', '/')
  vi.mocked(modulesApi.listModules).mockResolvedValue([])
})

describe('route-level code splitting', () => {
  it('mantém o Shell e o fallback durante o carregamento lazy de Cadastros', async () => {
    visit('/customers')

    expect(screen.getByTestId('app-shell')).toBeTruthy()
    expect(screen.getByRole('status').textContent).toContain('Carregando página...')

    resolveCadastros()
    expect(await screen.findByText('Clientes lazy')).toBeTruthy()
  })

  it.each([
    { path: '/customers', text: 'Clientes lazy' },
    { path: '/sales/new', text: 'Nova venda lazy' },
    { path: '/sales', text: 'Vendas lazy' },
    { path: '/commercial/quotes', text: 'Orçamentos lazy' },
    { path: '/purchases/receipts', text: 'Recebimentos' },
    { path: '/inventory/balances', text: 'Saldos lazy' },
    { path: '/finance/cashflow', text: 'Caixa lazy' },
  ])('carrega a família lazy para a rota $path', async ({ path, text }) => {
    visit(path)
    expect(await screen.findByText(text)).toBeTruthy()
  })

  it('preserva o bloqueio de acesso a módulos desativados', async () => {
    vi.mocked(modulesApi.listModules).mockResolvedValue([
      { id: 1, codigo: 'finance', nome: 'Financeiro', ativo: false, ordem: 1 },
    ])

    visit('/finance/cashflow')

    expect(await screen.findByText('Módulo desativado')).toBeTruthy()
    expect(screen.queryByText('Caixa lazy')).toBeNull()
  })

  it('mantém o Shell renderizado durante o carregamento lazy de Reports', async () => {
    visit('/reports/commercial')

    expect(screen.getByTestId('app-shell')).toBeTruthy()
    expect(screen.getByRole('status').textContent).toContain('Carregando página...')

    resolveReports()
    expect(await screen.findByText('Relatório comercial lazy')).toBeTruthy()
  })

  it('mantém o Dashboard eager e preserva o redirect legado sem carregar Reports', () => {
    visit('/')
    expect(screen.getByText('Dashboard imediato')).toBeTruthy()

    cleanup()
    visit('/reports/dashboard')
    expect(screen.getByText('Dashboard imediato')).toBeTruthy()
    expect(screen.queryByText('Relatório comercial lazy')).toBeNull()
  })

  it('carrega as rotas de Reports pela mesma família lazy', async () => {
    visit('/reports/finance')
    expect(await screen.findByText('Relatório financeiro lazy')).toBeTruthy()
  })

  it('carrega Settings sob demanda sem alterar suas rotas internas', async () => {
    visit('/settings')
    expect(await screen.findByText('Configurações lazy')).toBeTruthy()

    cleanup()
    visit('/settings/modules')
    expect(await screen.findByText('Módulos lazy')).toBeTruthy()
  })
})
