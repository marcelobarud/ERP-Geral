import { useCallback, useEffect, useState, type MouseEvent } from 'react'

import { ErrorState } from '../../components/ErrorState'
import { LoadingState } from '../../components/LoadingState'
import { PageHeader } from '../../components/PageHeader'
import { getDashboardSummary } from './api'
import { useCustomizable } from '../settings/VisualCustomizationContext'

type DashboardPageProps = {
  onNavigate: (path: string) => void
}

type DashboardCounts = {
  customers: number | null
  products: number | null
  suppliers: number | null
  employees: number | null
  sales: number | null
}

type SummaryCardProps = {
  label: string
  count: number | null
  description: string
  icon: string
  href: string
  onNavigate: (path: string) => void
  customizationKey: string
}

type QuickActionProps = {
  label: string
  description: string
  icon: string
  href: string
  onNavigate: (path: string) => void
  customizationKey: string
}

const initialCounts: DashboardCounts = {
  customers: null,
  products: null,
  suppliers: null,
  employees: null,
  sales: null,
}

function navigateFromLink(
  event: MouseEvent<HTMLAnchorElement>,
  href: string,
  onNavigate: (path: string) => void,
) {
  event.preventDefault()
  onNavigate(href)
}

function SummaryCard({
  label,
  count,
  description,
  icon,
  href,
  onNavigate,
  customizationKey,
}: SummaryCardProps) {
  const surfaceCustomization = useCustomizable({ key: customizationKey, type: 'SURFACE', group: 'summary-card', page: 'dashboard', label })
  const valueCustomization = useCustomizable({ key: `${customizationKey}.value`, type: 'TEXT', group: 'summary-value', page: 'dashboard', label: `${label} valor` })
  return (
    <a
      className="dashboard-summary-card"
      {...surfaceCustomization}
      href={href}
      onClick={(event) => navigateFromLink(event, href, onNavigate)}
    >
      <span className="dashboard-card-icon" aria-hidden="true">
        {icon}
      </span>
      <span className="dashboard-card-label">{label}</span>
      <strong className="dashboard-card-value" {...valueCustomization}>
        {count === null ? '—' : count}
      </strong>
      <span className="dashboard-card-description">{description}</span>
      <span className="dashboard-card-link">Acessar área →</span>
    </a>
  )
}

function QuickAction({
  label,
  description,
  icon,
  href,
  onNavigate,
  customizationKey,
}: QuickActionProps) {
  const buttonCustomization = useCustomizable({ key: customizationKey, type: 'BUTTON', group: 'quick-action', page: 'dashboard', label })
  return (
    <a
      className="dashboard-quick-action"
      {...buttonCustomization}
      href={href}
      onClick={(event) => navigateFromLink(event, href, onNavigate)}
    >
      <span className="dashboard-action-icon" aria-hidden="true">
        {icon}
      </span>
      <span>
        <strong>{label}</strong>
        <span>{description}</span>
      </span>
      <span className="dashboard-action-arrow" aria-hidden="true">
        →
      </span>
    </a>
  )
}

export function DashboardPage({ onNavigate }: DashboardPageProps) {
  const [counts, setCounts] = useState<DashboardCounts>(initialCounts)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  const loadDashboard = useCallback(async () => {
    setLoading(true)
    setLoadError(null)

    try {
      setCounts(await getDashboardSummary())
    } catch {
      setCounts(initialCounts)
      setLoadError('Algumas informações não puderam ser carregadas. Tente novamente.')
    }

    setLoading(false)
  }, [])

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect
    void loadDashboard()
  }, [loadDashboard])

  return (
    <div className="dashboard-page">
      <PageHeader
        eyebrow="Visão geral"
        title="Olá, que bom ter você aqui."
        description="Acompanhe o estado atual do ERP e acesse rapidamente o que precisa ser feito."
        pageId="dashboard"
      />

      {loading ? <LoadingState label="Carregando resumo operacional..." /> : null}
      {loadError ? <ErrorState description={loadError} onRetry={() => void loadDashboard()} /> : null}

      {!loading ? (
        <>
          <section className="dashboard-section dashboard-actions-section" aria-labelledby="dashboard-actions-title">
            <div className="dashboard-section-heading">
              <div>
                <p className="eyebrow">Atalhos</p>
                <h2 id="dashboard-actions-title">Próximos passos</h2>
              </div>
            </div>
            <div className="dashboard-actions-grid">
              <QuickAction label="Nova venda" description="Registre uma venda com um ou mais produtos." icon="+" href="/sales/new" onNavigate={onNavigate} customizationKey="dashboard.quick_action.new_sale" />
              <QuickAction label="Abrir vendas" description="Consulte o histórico e os preços aplicados." icon="↗" href="/sales" onNavigate={onNavigate} customizationKey="dashboard.quick_action.sales" />
              <QuickAction label="Configurar aparência" description="Ajuste nome, logo e identidade visual." icon="◌" href="/settings/appearance" onNavigate={onNavigate} customizationKey="dashboard.quick_action.appearance" />
              <QuickAction label="Revisar módulos" description="Escolha as áreas ativas nesta instalação." icon="◈" href="/settings/modules" onNavigate={onNavigate} customizationKey="dashboard.quick_action.modules" />
            </div>
          </section>

          <section className="dashboard-section" aria-labelledby="dashboard-summary-title">
            <div className="dashboard-section-heading">
              <div>
                <p className="eyebrow">Agora</p>
                <h2 id="dashboard-summary-title">Resumo operacional</h2>
              </div>
              <span className="dashboard-section-note">Dados das listagens atuais</span>
            </div>
            <div className="dashboard-summary-grid">
              <SummaryCard label="Clientes" count={counts.customers} description={counts.customers === 0 ? 'Nenhum cliente cadastrado' : 'Pessoas cadastradas'} icon="◎" href="/customers" onNavigate={onNavigate} customizationKey="dashboard.summary.customers.card" />
              <SummaryCard label="Produtos" count={counts.products} description={counts.products === 0 ? 'Nenhum produto cadastrado' : 'Itens no catálogo'} icon="▦" href="/products" onNavigate={onNavigate} customizationKey="dashboard.summary.products.card" />
              <SummaryCard label="Fornecedores" count={counts.suppliers} description={counts.suppliers === 0 ? 'Nenhum fornecedor cadastrado' : 'Parceiros cadastrados'} icon="◈" href="/suppliers" onNavigate={onNavigate} customizationKey="dashboard.summary.suppliers.card" />
              <SummaryCard label="Funcionários" count={counts.employees} description={counts.employees === 0 ? 'Nenhum funcionário cadastrado' : 'Equipe cadastrada'} icon="♙" href="/employees" onNavigate={onNavigate} customizationKey="dashboard.summary.employees.card" />
              <SummaryCard label="Vendas" count={counts.sales} description={counts.sales === 0 ? 'Nenhuma venda registrada' : 'Vendas no histórico'} icon="↗" href="/sales" onNavigate={onNavigate} customizationKey="dashboard.summary.sales.card" />
            </div>
          </section>
        </>
      ) : null}
    </div>
  )
}
