// @vitest-environment jsdom

import type { ReactNode } from 'react'
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

const { reportsReady, resolveReports } = vi.hoisted(() => {
  let resolve: (() => void) | undefined
  const ready = new Promise<void>((nextResolve) => { resolve = nextResolve })
  return { reportsReady: ready, resolveReports: () => resolve?.() }
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
vi.mock('../features/customers/CustomersPage', () => ({ CustomersPage: () => <div>Clientes</div> }))
vi.mock('../features/employees/EmployeesPage', () => ({ EmployeesPage: () => <div>Funcionários</div> }))
vi.mock('../features/products/ProductsPage', () => ({ ProductsPage: () => <div>Produtos</div> }))
vi.mock('../features/sales/SalesPages', () => ({ NewSalePage: () => <div>Nova venda</div>, SalesPage: () => <div>Vendas</div> }))
vi.mock('../features/suppliers/SuppliersPage', () => ({ SuppliersPage: () => <div>Fornecedores</div> }))
vi.mock('../features/commercial/CommercialPages', () => ({ OrdersPage: () => <div>Pedidos</div>, QuotesPage: () => <div>Orçamentos</div>, ReturnsPage: () => <div>Devoluções</div> }))
vi.mock('../features/purchases/PurchasesPages', () => ({ PurchasesPage: () => <div>Compras</div>, ReceiptsPage: () => <div>Recebimentos</div> }))
vi.mock('../features/inventory/InventoryPages', () => ({ AdjustmentsPage: () => <div>Ajustes</div>, BalancesPage: () => <div>Saldos</div>, DepositsPage: () => <div>Depósitos</div>, InventoriesPage: () => <div>Inventários</div>, MovementsPage: () => <div>Movimentações</div> }))
vi.mock('../features/finance/FinancePages', () => ({ CashflowPage: () => <div>Caixa</div>, FinancialTitlesPage: () => <div>Títulos</div> }))
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
})

describe('route-level code splitting', () => {
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
