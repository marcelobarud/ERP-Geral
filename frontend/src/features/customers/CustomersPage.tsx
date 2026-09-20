import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from 'react'

import { ConfirmDialog } from '../../components/ConfirmDialog'
import { actionIcons, iconSizes, iconStroke } from '../../app/iconography'
import { EmptyState } from '../../components/EmptyState'
import { ErrorState } from '../../components/ErrorState'
import { FeedbackBanner } from '../../components/FeedbackBanner'
import { FilterMenu } from '../../components/FilterMenu'
import { uniqueFilterOptions } from '../../components/filterOptions'
import { LoadingState } from '../../components/LoadingState'
import { Modal } from '../../components/Modal'
import { PaginationControls } from '../../components/PaginationControls'
import { PageHeader } from '../../components/PageHeader'
import { SearchInput } from '../../components/SearchInput'
import { getApiErrorMessage } from '../../services/httpClient'
import { getPaginationMeta, type PaginationMeta } from '../../types/pagination'
import { CustomFieldDetails, CustomFieldFields } from '../customFields/CustomFieldFields'
import { useCustomizable } from '../settings/VisualCustomizationContext'
import {
  createCustomer,
  deleteCustomer,
  getCustomer,
  listCustomers,
  updateCustomer,
} from './api'
import type { Customer, CustomerDetails, CustomerPayload } from './types'
import type { CustomerListFilters } from './api'

const RemoveFilterIcon = actionIcons.close

const emptyCustomer: CustomerPayload = {
  nome: '',
  cidade: '',
  estado: '',
  rua: '',
  numero: '',
  complemento: '',
}

const PAGE_SIZE = 20

type CustomerFormProps = {
  initialValue: CustomerPayload
  saving: boolean
  onCancel: () => void
  onSave: (payload: CustomerPayload) => void
}

type CustomerFilterKey = 'search' | 'city' | 'state'

type ActiveCustomerFilter = {
  key: CustomerFilterKey
  label: string
  value: string
}

function CustomerForm({ initialValue, saving, onCancel, onSave }: CustomerFormProps) {
  const [form, setForm] = useState({ ...initialValue, complemento: initialValue.complemento ?? '' })
  const [customValues, setCustomValues] = useState<Record<string, unknown>>({})

  const updateField = (field: keyof CustomerPayload, value: string) => {
    setForm((current) => ({ ...current, [field]: value }))
  }

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    onSave({ ...form, complemento: form.complemento.trim() || null, ...(Object.keys(customValues).length ? { campos_personalizados: customValues } : {}) })
  }

  return (
    <form onSubmit={submit}>
      <div className="form-grid">
        <div className="form-field form-grid-wide"><label htmlFor="customer-name">Nome</label><input id="customer-name" required value={form.nome} onChange={(event) => updateField('nome', event.target.value)} /></div>
        <div className="form-field"><label htmlFor="customer-city">Cidade</label><input id="customer-city" required value={form.cidade} onChange={(event) => updateField('cidade', event.target.value)} /></div>
        <div className="form-field"><label htmlFor="customer-state">Estado</label><input id="customer-state" required maxLength={2} value={form.estado} onChange={(event) => updateField('estado', event.target.value.toUpperCase())} /></div>
        <div className="form-field"><label htmlFor="customer-street">Rua</label><input id="customer-street" required value={form.rua} onChange={(event) => updateField('rua', event.target.value)} /></div>
        <div className="form-field"><label htmlFor="customer-number">Número</label><input id="customer-number" required value={form.numero} onChange={(event) => updateField('numero', event.target.value)} /></div>
        <div className="form-field form-grid-wide"><label htmlFor="customer-complement">Complemento (opcional)</label><input id="customer-complement" value={form.complemento ?? ''} onChange={(event) => updateField('complemento', event.target.value)} /></div>
        <CustomFieldFields module="customers" values={customValues} onChange={(name, value) => setCustomValues((current) => ({ ...current, [name]: value }))} />
      </div>
      <div className="form-actions"><button className="button button-secondary" type="button" onClick={onCancel} disabled={saving}>Cancelar</button><button className="button button-primary" type="submit" disabled={saving}>{saving ? 'Salvando...' : 'Salvar cliente'}</button></div>
    </form>
  )
}

function formatQuantity(quantity: string): string {
  return quantity.replace('.', ',')
}

function CustomerDetails({ customer }: { customer: CustomerDetails }) {
  return (
    <>
      <dl className="detail-grid">
        <div><dt>Nome</dt><dd>{customer.nome}</dd></div><div><dt>Cidade / Estado</dt><dd>{customer.cidade} / {customer.estado}</dd></div><div><dt>Rua</dt><dd>{customer.rua}</dd></div><div><dt>Número</dt><dd>{customer.numero}</dd></div><div className="form-grid-wide"><dt>Complemento</dt><dd>{customer.complemento || 'Não informado'}</dd></div>
      </dl><CustomFieldDetails values={customer.campos_personalizados} />
      <section className="relational-detail-section" aria-labelledby="customer-purchased-products-title">
        <div className="relational-detail-heading">
          <h3 id="customer-purchased-products-title">Produtos comprados</h3>
          <span>{customer.produtos_comprados.length} {customer.produtos_comprados.length === 1 ? 'produto' : 'produtos'}</span>
        </div>
        {customer.produtos_comprados.length === 0 ? <p className="relational-detail-empty">Nenhum produto comprado.</p> : <ul className="relational-detail-list">{customer.produtos_comprados.map((product) => <li className="relational-detail-item" key={product.produto_id}><strong>{product.nome}</strong><span>Quantidade: {formatQuantity(product.quantidade)}</span></li>)}</ul>}
      </section>
    </>
  )
}

function CustomerListLoading() {
  return (
    <div className="customers-loading-layout">
      <LoadingState label="Carregando clientes..." />
      <div className="customers-table-skeleton" aria-hidden="true">
        {Array.from({ length: 6 }, (_, index) => <span key={index} />)}
      </div>
    </div>
  )
}

export function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [filterCustomers, setFilterCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchDraft, setSearchDraft] = useState('')
  const [cityDraft, setCityDraft] = useState('')
  const [stateDraft, setStateDraft] = useState('')
  const [appliedFilters, setAppliedFilters] = useState<CustomerListFilters>({})
  const [page, setPage] = useState(1)
  const [pagination, setPagination] = useState<PaginationMeta>({ page: 1, page_size: PAGE_SIZE, total: 0, total_pages: 0 })
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [feedback, setFeedback] = useState<{ kind: 'success' | 'error'; message: string } | null>(null)
  const [modal, setModal] = useState<'create' | 'edit' | 'view' | null>(null)
  const [selected, setSelected] = useState<Customer | null>(null)
  const [selectedDetails, setSelectedDetails] = useState<CustomerDetails | null>(null)
  const [detailsLoading, setDetailsLoading] = useState(false)
  const [detailsError, setDetailsError] = useState<string | null>(null)
  const createButtonCustomization = useCustomizable({ key: 'customers.create_button', type: 'BUTTON', group: 'primary-action', page: 'customers', label: 'Novo cliente' })
  const tableCustomization = useCustomizable({ key: 'customers.table', type: 'TABLE', group: 'data-table', page: 'customers', label: 'Tabela de clientes' })
  const [saving, setSaving] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<Customer | null>(null)
  const [deleting, setDeleting] = useState(false)
  const loadRequestId = useRef(0)

  const loadCustomers = useCallback(async () => {
    const requestId = ++loadRequestId.current
    setLoading(true)
    setError(null)
    try {
      const [customerList, optionList] = await Promise.all([
        listCustomers({ ...appliedFilters, page, pageSize: PAGE_SIZE }),
        listCustomers({ page: 1, pageSize: 100 }),
      ])
      if (requestId !== loadRequestId.current) return
      setCustomers(customerList)
      setFilterCustomers(optionList)
      setPagination(getPaginationMeta(customerList))
    } catch (loadError) { if (requestId === loadRequestId.current) setError(getApiErrorMessage(loadError, 'Não foi possível carregar os clientes.')) } finally { if (requestId === loadRequestId.current) setLoading(false) }
  }, [appliedFilters, page])

  // oxlint-disable-next-line
  useEffect(() => { void loadCustomers() }, [loadCustomers])

  const hasDraftFilters = Boolean(searchDraft.trim() || cityDraft || stateDraft)
  const activeFilters: ActiveCustomerFilter[] = [
    appliedFilters.search ? { key: 'search', label: 'Busca', value: appliedFilters.search } : null,
    appliedFilters.city ? { key: 'city', label: 'Cidade', value: appliedFilters.city } : null,
    appliedFilters.state ? { key: 'state', label: 'Estado', value: appliedFilters.state } : null,
  ].filter((filter): filter is ActiveCustomerFilter => filter !== null)
  const hasAppliedFilters = activeFilters.length > 0
  const filterCities = useMemo(() => uniqueFilterOptions(filterCustomers.map((customer) => customer.cidade)), [filterCustomers])
  const filterStates = useMemo(() => uniqueFilterOptions(filterCustomers.map((customer) => customer.estado)), [filterCustomers])
  const applyFilters = () => { setPage(1); setAppliedFilters({ search: searchDraft.trim(), city: cityDraft, state: stateDraft }); setFiltersOpen(false) }
  const clearFilters = () => { setPage(1); setSearchDraft(''); setCityDraft(''); setStateDraft(''); setAppliedFilters({}); setFiltersOpen(false) }
  const removeFilter = (key: CustomerFilterKey) => {
    setPage(1)
    if (key === 'search') setSearchDraft('')
    if (key === 'city') setCityDraft('')
    if (key === 'state') setStateDraft('')
    setAppliedFilters((current) => {
      const next = { ...current }
      delete next[key]
      return next
    })
  }

  const openCustomerDetails = async (customer: Customer) => {
    setSelected(customer)
    setSelectedDetails(null)
    setDetailsError(null)
    setDetailsLoading(true)
    setModal('view')
    try {
      setSelectedDetails(await getCustomer(customer.id))
    } catch (loadError) {
      setDetailsError(getApiErrorMessage(loadError, 'Não foi possível carregar os detalhes do cliente.'))
    } finally {
      setDetailsLoading(false)
    }
  }

  const saveCustomer = async (payload: CustomerPayload) => {
    setSaving(true)
    setFeedback(null)
    try {
      const saved = selected ? await updateCustomer(selected.id, payload) : await createCustomer(payload)
      setCustomers((current) => selected ? current.map((item) => item.id === saved.id ? saved : item) : [...current, saved])
      setFilterCustomers((current) => selected ? current.map((item) => item.id === saved.id ? saved : item) : [...current, saved])
      setModal(null)
      setSelected(null)
      setFeedback({ kind: 'success', message: selected ? 'Cliente atualizado com sucesso.' : 'Cliente criado com sucesso.' })
    } catch (saveError) { setFeedback({ kind: 'error', message: getApiErrorMessage(saveError, 'Não foi possível salvar o cliente.') }) } finally { setSaving(false) }
  }

  const removeCustomer = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    setFeedback(null)
    try { await deleteCustomer(deleteTarget.id); setCustomers((current) => current.filter((item) => item.id !== deleteTarget.id)); setFilterCustomers((current) => current.filter((item) => item.id !== deleteTarget.id)); setFeedback({ kind: 'success', message: 'Cliente excluído com sucesso.' }) } catch (deleteError) { setFeedback({ kind: 'error', message: getApiErrorMessage(deleteError, 'Não foi possível excluir o cliente.') }) } finally { setDeleting(false); setDeleteTarget(null) }
  }

  const formValue: CustomerPayload = selected
    ? (({ id: _id, campos_personalizados: _custom, ...payload }) => payload)(selected)
    : emptyCustomer

  return (
    <div className="crud-page customers-page">
      <div className="crud-page-header"><PageHeader eyebrow="Cadastros" title="Clientes" description="Organize as pessoas que fazem parte do seu negócio." pageId="customers" /><button className="button button-primary" type="button" {...createButtonCustomization} onClick={() => { setSelected(null); setModal('create'); setFeedback(null) }}>+ Novo cliente</button></div>
      {feedback ? <FeedbackBanner kind={feedback.kind} message={feedback.message} onDismiss={() => setFeedback(null)} /> : null}
      <section className="filter-toolbar customers-filter-toolbar" aria-label="Filtros de clientes">
        <SearchInput value={searchDraft} onChange={setSearchDraft} onSearch={(value) => { setPage(1); setAppliedFilters((current) => { const search = value.trim(); if (current.search === search) return current; const { search: _search, ...filters } = current; return search ? { ...filters, search } : filters }) }} onClear={() => setSearchDraft('')} label="Pesquisar clientes" customizationKey="customers.search_input" customizationPage="customers" />
        <FilterMenu activeCount={activeFilters.length} canClear={hasDraftFilters || hasAppliedFilters} open={filtersOpen} onToggle={() => setFiltersOpen((current) => !current)} onClose={() => setFiltersOpen(false)} onApply={applyFilters} onClear={clearFilters}>
          <label className="filter-field">Cidade<select value={cityDraft} onChange={(event) => setCityDraft(event.target.value)}><option value="">Todas as cidades</option>{filterCities.map((city) => <option value={city} key={city}>{city}</option>)}</select></label>
          <label className="filter-field">Estado<select value={stateDraft} onChange={(event) => setStateDraft(event.target.value)}><option value="">Todos os estados</option>{filterStates.map((state) => <option value={state} key={state}>{state}</option>)}</select></label>
        </FilterMenu>
      </section>
      {activeFilters.length ? (
        <div className="customers-active-filters" aria-label="Filtros ativos">
          <span className="customers-active-filters-label">Filtros ativos</span>
          {activeFilters.map((filter) => (
            <button className="customers-filter-chip" type="button" key={filter.key} onClick={() => removeFilter(filter.key)}>
              <span>{filter.label}: {filter.value}</span>
              <span aria-hidden="true"><RemoveFilterIcon size={iconSizes.status} stroke={iconStroke} focusable="false" /></span>
              <span className="sr-only">Remover filtro {filter.label}</span>
            </button>
          ))}
          <button className="text-button customers-clear-filters" type="button" onClick={clearFilters}>Limpar filtros</button>
        </div>
      ) : null}
      {loading ? <CustomerListLoading /> : error ? <ErrorState description={error} onRetry={() => void loadCustomers()} /> : customers.length === 0 ? <div className="data-card customers-empty-state"><EmptyState title={hasAppliedFilters ? 'Nenhum resultado encontrado para os filtros aplicados.' : 'Nenhum cliente cadastrado ainda'} description={hasAppliedFilters ? 'Ajuste a busca ou remova os filtros ativos para ver outros clientes.' : 'Crie o primeiro cliente usando a ação Novo cliente acima.'} /></div> : <><div className="data-card data-table-wrap customers-table"><table className="data-table" {...tableCustomization}><thead><tr><th>Cliente</th><th>Localização</th><th>Endereço</th><th><span className="sr-only">Ações</span></th></tr></thead><tbody>{customers.map((customer) => <tr key={customer.id}><td className="data-primary">{customer.nome}<span className="data-secondary">ID {customer.id}</span></td><td>{customer.cidade} / {customer.estado}</td><td>{customer.rua}, {customer.numero}</td><td><div className="table-actions"><button className="table-action" type="button" onClick={() => void openCustomerDetails(customer)}>Ver</button><button className="table-action" type="button" onClick={() => { setSelected(customer); setModal('edit') }}>Editar</button><button className="table-action table-action-danger" type="button" onClick={() => setDeleteTarget(customer)}>Excluir</button></div></td></tr>)}</tbody></table></div><PaginationControls meta={pagination} onPageChange={setPage} /></>}
      {modal === 'view' && selected ? <Modal title="Detalhes do cliente" size="large" onClose={() => { setModal(null); setSelectedDetails(null) }}>{detailsLoading ? <LoadingState label="Carregando detalhes do cliente..." /> : detailsError ? <ErrorState description={detailsError} onRetry={() => void openCustomerDetails(selected)} /> : selectedDetails ? <CustomerDetails customer={selectedDetails} /> : null}</Modal> : null}
      {(modal === 'create' || modal === 'edit') ? <Modal title={modal === 'edit' ? 'Editar cliente' : 'Novo cliente'} description="Preencha os campos obrigatórios para continuar." onClose={() => setModal(null)}><CustomerForm initialValue={formValue} saving={saving} onCancel={() => setModal(null)} onSave={(payload) => void saveCustomer(payload)} /></Modal> : null}
      {deleteTarget ? <ConfirmDialog title="Excluir cliente?" description={`O cadastro de ${deleteTarget.nome} será removido. Essa ação não pode ser desfeita.`} busy={deleting} onCancel={() => setDeleteTarget(null)} onConfirm={() => void removeCustomer()} /> : null}
    </div>
  )
}
