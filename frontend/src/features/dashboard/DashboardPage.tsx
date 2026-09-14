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
  href: string
  onNavigate: (path: string) => void
  customizationKey: string
}

type QuickActionProps = {
  label: string
  description: string
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
  href,
  onNavigate,
  customizationKey,
}: SummaryCardProps) {
  const surfaceCustomization = useCustomizable({ key: customizationKey, type: 'SURFACE', group: 'summary-card', page: 'dashboard', label })
  const valueCustomization = useCustomizable({ key: `${customizationKey}.value`, type: 'TEXT', group: 'summary-value', page: 'dashboard', label: `${label} valor` })
  return (
    <article
      className="dashboard-metric"
      {...surfaceCustomization}
    >
      <a
        className="dashboard-metric-label"
        href={href}
        onClick={(event) => navigateFromLink(event, href, onNavigate)}
      >
        {label}
      </a>
      <strong className="dashboard-metric-value" {...valueCustomization}>
        {count === null ? '—' : count}
      </strong>
      <span className="dashboard-metric-context">{description}</span>
    </article>
  )
}

function QuickAction({
  label,
  description,
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
      <span className="dashboard-quick-action-copy">
        <strong>{label}</strong>
        <span>{description}</span>
      </span>
      <span className="dashboard-action-arrow" aria-hidden="true">
        →
      </span>
    </a>
  )
}

function DashboardLoading() {
  return (
    <div className="dashboard-loading-layout">
      <LoadingState label="Carregando resumo operacional..." />
      <div className="dashboard-loading-skeleton" aria-hidden="true">
        <div className="dashboard-loading-section">
          <span className="dashboard-skeleton-heading" />
          <div className="dashboard-skeleton-metrics">
            {Array.from({ length: 5 }, (_, index) => <span className="dashboard-skeleton-metric" key={index} />)}
          </div>
        </div>
        <div className="dashboard-loading-section">
          <span className="dashboard-skeleton-heading dashboard-skeleton-heading-short" />
          <div className="dashboard-skeleton-actions">
            {Array.from({ length: 4 }, (_, index) => <span className="dashboard-skeleton-action" key={index} />)}
          </div>
        </div>
      </div>
    </div>
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
        title="Visão geral do ERP"
        description="Entenda o estado atual da operação e escolha onde investigar ou agir."
        pageId="dashboard"
      />

      {loading ? <DashboardLoading /> : null}

      {!loading ? (
        <>
          <section className="dashboard-section dashboard-overview" aria-labelledby="dashboard-summary-title">
            <div className="dashboard-section-heading">
              <div>
                <p className="eyebrow">Estado geral</p>
                <h2 id="dashboard-summary-title">Resumo operacional</h2>
              </div>
              <span className="dashboard-section-note">Contagens das listagens atuais</span>
            </div>
            {loadError ? <ErrorState description={loadError} onRetry={() => void loadDashboard()} /> : null}
            <div className="dashboard-metrics">
              <SummaryCard label="Clientes" count={counts.customers} description={counts.customers === null ? 'Indisponível no momento' : counts.customers === 0 ? 'Nenhum cliente cadastrado' : 'Pessoas cadastradas'} href="/customers" onNavigate={onNavigate} customizationKey="dashboard.summary.customers.card" />
              <SummaryCard label="Produtos" count={counts.products} description={counts.products === null ? 'Indisponível no momento' : counts.products === 0 ? 'Nenhum produto cadastrado' : 'Itens no catálogo'} href="/products" onNavigate={onNavigate} customizationKey="dashboard.summary.products.card" />
              <SummaryCard label="Fornecedores" count={counts.suppliers} description={counts.suppliers === null ? 'Indisponível no momento' : counts.suppliers === 0 ? 'Nenhum fornecedor cadastrado' : 'Parceiros cadastrados'} href="/suppliers" onNavigate={onNavigate} customizationKey="dashboard.summary.suppliers.card" />
              <SummaryCard label="Funcionários" count={counts.employees} description={counts.employees === null ? 'Indisponível no momento' : counts.employees === 0 ? 'Nenhum funcionário cadastrado' : 'Equipe cadastrada'} href="/employees" onNavigate={onNavigate} customizationKey="dashboard.summary.employees.card" />
              <SummaryCard label="Vendas" count={counts.sales} description={counts.sales === null ? 'Indisponível no momento' : counts.sales === 0 ? 'Nenhuma venda registrada' : 'Vendas no histórico'} href="/sales" onNavigate={onNavigate} customizationKey="dashboard.summary.sales.card" />
            </div>
          </section>

          <section className="dashboard-section dashboard-actions-section" aria-labelledby="dashboard-actions-title">
            <div className="dashboard-section-heading">
              <div>
                <p className="eyebrow">Navegação</p>
                <h2 id="dashboard-actions-title">Próximos passos</h2>
              </div>
            </div>
            <nav className="dashboard-actions-grid" aria-label="Atalhos do dashboard">
              <QuickAction label="Nova venda" description="Registre uma venda com um ou mais produtos." href="/sales/new" onNavigate={onNavigate} customizationKey="dashboard.quick_action.new_sale" />
              <QuickAction label="Abrir vendas" description="Consulte o histórico e os preços aplicados." href="/sales" onNavigate={onNavigate} customizationKey="dashboard.quick_action.sales" />
              <QuickAction label="Configurar aparência" description="Ajuste nome, logo e identidade visual." href="/settings/appearance" onNavigate={onNavigate} customizationKey="dashboard.quick_action.appearance" />
              <QuickAction label="Revisar módulos" description="Escolha as áreas ativas nesta instalação." href="/settings/modules" onNavigate={onNavigate} customizationKey="dashboard.quick_action.modules" />
            </nav>
          </section>
        </>
      ) : null}
    </div>
  )
}
