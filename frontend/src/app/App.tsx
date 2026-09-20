import { useCallback, useEffect, useMemo, useState } from 'react'

import { AppLayout } from '../components/AppLayout'
import { DashboardPage } from '../features/dashboard/DashboardPage'
import { CustomersPage } from '../features/customers/CustomersPage'
import { EmployeesPage } from '../features/employees/EmployeesPage'
import { ProductsPage } from '../features/products/ProductsPage'
import { NewSalePage, SalesPage } from '../features/sales/SalesPages'
import { SuppliersPage } from '../features/suppliers/SuppliersPage'
import { AppearancePage } from '../features/settings/AppearancePage'
import { AppearanceProvider, useAppearance } from '../features/settings/AppearanceContext'
import { AuthProvider, useAuth } from '../features/auth/AuthContext'
import { LoginPage } from '../features/auth/LoginPage'
import { SetupPage } from '../features/auth/SetupPage'
import { CustomFieldsPage } from '../features/settings/CustomFieldsPage'
import { OrdersPage, PaymentConditionsPage, QuotesPage, ReturnsPage } from '../features/commercial/CommercialPages'
import { PurchasesPage, ReceiptsPage } from '../features/purchases/PurchasesPages'
import { AdjustmentsPage, BalancesPage, DepositsPage, InventoriesPage, MovementsPage } from '../features/inventory/InventoryPages'
import { CashflowPage, FinancialTitlesPage } from '../features/finance/FinancePages'
import { CommercialReportPage, FinanceReportPage, PurchasesReportPage, StockReportPage } from '../features/reports/ReportsPages'
import { ModulesPage } from '../features/settings/ModulesPage'
import { SettingsHubPage } from '../features/settings/SettingsHubPage'
import { UsersPage } from '../features/settings/UsersPage'
import { listModules, type ErpModule } from '../features/settings/modulesApi'
import { VisualCustomizationProvider } from '../features/settings/VisualCustomizationContext'
import { appearanceLabels, pageIdForPath } from '../features/settings/types'
import { ModuleDisabledPage, NotFoundPage } from '../pages/NotFoundPage'
import { navigationIcons } from './iconography'
import { getCanonicalPathname, getModuleForPath, getRoute, type RouteDefinition } from './routes'

function currentPathname(): string {
  return getCanonicalPathname(window.location.pathname || '/')
}

function PageForRoute({
  route,
  onNavigate,
  canManageUsers,
}: {
  route: RouteDefinition
  onNavigate: (path: string) => void
  canManageUsers: boolean
}) {
  switch (route.path) {
    case '/':
      return <DashboardPage onNavigate={onNavigate} />
    case '/customers':
      return <CustomersPage />
    case '/products':
      return <ProductsPage />
    case '/suppliers':
      return <SuppliersPage />
    case '/employees':
      return <EmployeesPage />
    case '/sales/new':
      return <NewSalePage />
    case '/sales':
      return <SalesPage />
    case '/commercial/quotes':
      return <QuotesPage />
    case '/commercial/orders':
      return <OrdersPage />
    case '/commercial/sales':
      return <SalesPage />
    case '/commercial/returns':
      return <ReturnsPage />
    case '/purchases':
      return <PurchasesPage />
    case '/purchases/receipts':
      return <ReceiptsPage />
    case '/inventory/balances':
      return <BalancesPage />
    case '/inventory/movements':
      return <MovementsPage />
    case '/inventory/adjustments':
      return <AdjustmentsPage />
    case '/inventory/inventories':
      return <InventoriesPage />
    case '/inventory/deposits':
      return <DepositsPage />
    case '/finance/receivables':
      return <FinancialTitlesPage kind="RECEBER" />
    case '/finance/payables':
      return <FinancialTitlesPage kind="PAGAR" />
    case '/finance/cashflow':
      return <CashflowPage />
    case '/reports/commercial':
      return <CommercialReportPage />
    case '/reports/purchases':
      return <PurchasesReportPage />
    case '/reports/stock':
      return <StockReportPage />
    case '/reports/finance':
      return <FinanceReportPage />
    case '/settings':
      return <SettingsHubPage canManageUsers={canManageUsers} />
    case '/settings/appearance':
      return <AppearancePage />
    case '/settings/custom-fields':
      return <CustomFieldsPage />
    case '/settings/payment-conditions':
      return <PaymentConditionsPage />
    case '/settings/modules':
      return <ModulesPage />
    case '/settings/users':
      return <UsersPage />
    case '/module-disabled':
      return <ModuleDisabledPage />
    default:
      return <NotFoundPage />
  }
}

function AppContent() {
  const { preview, pageAppearances, loadPageAppearance } = useAppearance()
  const { authRequired, user } = useAuth()
  const [pathname, setPathname] = useState(currentPathname)
  const [modules, setModules] = useState<ErpModule[]>([])
  const activeModules = useMemo(() => new Set(modules.filter((module) => module.ativo).map((module) => module.codigo)), [modules])
  const loadModules = useCallback(async () => { try { setModules(await listModules()) } catch { /* A API continua protegendo os endpoints. */ } }, [])

  useEffect(() => {
    const syncPathname = () => {
      const actualPathname = window.location.pathname || '/'
      const canonicalPathname = getCanonicalPathname(actualPathname)
      if (actualPathname !== canonicalPathname) {
        window.history.replaceState({}, '', canonicalPathname)
      }
      setPathname(canonicalPathname)
    }

    syncPathname()
    window.addEventListener('popstate', syncPathname)

    return () => window.removeEventListener('popstate', syncPathname)
  }, [])

  useEffect(() => {
    void loadModules()
    const reload = () => void loadModules()
    window.addEventListener('erp-modules-changed', reload)
    return () => window.removeEventListener('erp-modules-changed', reload)
  }, [loadModules])

  const navigate = useCallback(
    (path: string) => {
      const canonicalPath = getCanonicalPathname(path)
      if (canonicalPath === pathname) return

      window.history.pushState({}, '', canonicalPath)
      setPathname(canonicalPath)
    },
    [pathname],
  )

  const moduleCode = getModuleForPath(pathname)
  const moduleDisabled = modules.length > 0 && moduleCode !== null && !activeModules.has(moduleCode)
  const route = moduleDisabled ? { path: '/module-disabled', label: 'Módulo desativado', icon: navigationIcons.alert, description: 'Esta área está desativada nas configurações do ERP.' } : getRoute(pathname, appearanceLabels(preview))
  const pageId = pageIdForPath(pathname)
  const canManageUsers = !authRequired || user?.role === 'ADMIN'

  useEffect(() => {
    void loadPageAppearance(pageId)
  }, [loadPageAppearance, pageId])

  return (
      <AppLayout route={route} onNavigate={navigate} activeModules={activeModules.size ? activeModules : undefined} canManageUsers={canManageUsers} pageTheme={pageAppearances[pageId]?.resolved}>
      <PageForRoute route={route} onNavigate={navigate} canManageUsers={canManageUsers} />
    </AppLayout>
  )
}

function App() {
  return <AuthProvider><AuthenticatedApp /></AuthProvider>
}

function AuthenticatedApp() {
  const { authRequired, bootstrapAvailable, loading, user } = useAuth()

  if (loading) {
    return <div className="auth-loading" role="status">Carregando acesso...</div>
  }
  if (authRequired && !user) {
    return window.location.pathname === '/setup' && bootstrapAvailable ? <SetupPage /> : <LoginPage />
  }

  return <AppearanceProvider><VisualCustomizationProvider><AppContent /></VisualCustomizationProvider></AppearanceProvider>
}

export default App
