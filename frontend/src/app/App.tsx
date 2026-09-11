import { useCallback, useEffect, useState } from 'react'

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
import { CustomFieldsPage } from '../features/settings/CustomFieldsPage'
import { OrdersPage, PaymentConditionsPage, QuotesPage, ReturnsPage } from '../features/commercial/CommercialPages'
import { PurchasesPage, ReceiptsPage } from '../features/purchases/PurchasesPages'
import { VisualCustomizationProvider } from '../features/settings/VisualCustomizationContext'
import { appearanceLabels, pageIdForPath } from '../features/settings/types'
import { NotFoundPage } from '../pages/NotFoundPage'
import { getRoute, type RouteDefinition } from './routes'

function currentPathname(): string {
  return window.location.pathname || '/'
}

function PageForRoute({
  route,
  onNavigate,
}: {
  route: RouteDefinition
  onNavigate: (path: string) => void
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
    case '/settings/appearance':
      return <AppearancePage />
    case '/settings/custom-fields':
      return <CustomFieldsPage />
    case '/settings/payment-conditions':
      return <PaymentConditionsPage />
    default:
      return <NotFoundPage />
  }
}

function AppContent() {
  const { preview, pageAppearances, loadPageAppearance } = useAppearance()
  const [pathname, setPathname] = useState(currentPathname)

  useEffect(() => {
    const handlePopState = () => setPathname(currentPathname())
    window.addEventListener('popstate', handlePopState)

    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  const navigate = useCallback(
    (path: string) => {
      if (path === pathname) return

      window.history.pushState({}, '', path)
      setPathname(path)
    },
    [pathname],
  )

  const route = getRoute(pathname, appearanceLabels(preview))
  const pageId = pageIdForPath(pathname)

  useEffect(() => {
    void loadPageAppearance(pageId)
  }, [loadPageAppearance, pageId])

  return (
    <AppLayout route={route} onNavigate={navigate} pageTheme={pageAppearances[pageId]?.resolved}>
      <PageForRoute route={route} onNavigate={navigate} />
    </AppLayout>
  )
}

function App() {
  return <AuthProvider><AuthenticatedApp /></AuthProvider>
}

function AuthenticatedApp() {
  const { authRequired, loading, user } = useAuth()

  if (loading) {
    return <div className="auth-loading" role="status">Carregando acesso...</div>
  }
  if (authRequired && !user) return <LoginPage />

  return <AppearanceProvider><VisualCustomizationProvider><AppContent /></VisualCustomizationProvider></AppearanceProvider>
}

export default App
