import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from 'react'

import { ConfirmDialog } from '../../components/ConfirmDialog'
import { ActiveFilters, type ActiveFilterItem } from '../../components/ActiveFilters'
import { CadastrosListLoading } from '../../components/CadastrosListLoading'
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
import { createSupplier, deleteSupplier, getSupplier, listSuppliers, updateSupplier, type SupplierListFilters } from './api'
import type { Supplier, SupplierDetails, SupplierPayload } from './types'

const emptySupplier: SupplierPayload = { nome: '', cidade: '', estado: '', rua: '', numero: '', complemento: '', cnpj: '' }
const PAGE_SIZE = 20
type SupplierFilterKey = 'search' | 'city' | 'state'

function SupplierForm({ initialValue, saving, onCancel, onSave }: { initialValue: SupplierPayload; saving: boolean; onCancel: () => void; onSave: (payload: SupplierPayload) => void }) {
  const [form, setForm] = useState({ ...initialValue, complemento: initialValue.complemento ?? '' })
  const [customValues, setCustomValues] = useState<Record<string, unknown>>({})
  const updateField = (field: keyof SupplierPayload, value: string) => setForm((current) => ({ ...current, [field]: value }))
  const submit = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); onSave({ ...form, complemento: form.complemento.trim() || null, ...(Object.keys(customValues).length ? { campos_personalizados: customValues } : {}) }) }

  return <form onSubmit={submit}><div className="form-grid">
    <div className="form-field form-grid-wide"><label htmlFor="supplier-name">Nome</label><input id="supplier-name" required value={form.nome} onChange={(event) => updateField('nome', event.target.value)} /></div>
    <div className="form-field"><label htmlFor="supplier-cnpj">CNPJ</label><input id="supplier-cnpj" required value={form.cnpj} onChange={(event) => updateField('cnpj', event.target.value)} /></div>
    <div className="form-field"><label htmlFor="supplier-city">Cidade</label><input id="supplier-city" required value={form.cidade} onChange={(event) => updateField('cidade', event.target.value)} /></div>
    <div className="form-field"><label htmlFor="supplier-state">Estado</label><input id="supplier-state" required maxLength={2} value={form.estado} onChange={(event) => updateField('estado', event.target.value.toUpperCase())} /></div>
    <div className="form-field"><label htmlFor="supplier-street">Rua</label><input id="supplier-street" required value={form.rua} onChange={(event) => updateField('rua', event.target.value)} /></div>
    <div className="form-field"><label htmlFor="supplier-number">Número</label><input id="supplier-number" required value={form.numero} onChange={(event) => updateField('numero', event.target.value)} /></div>
    <div className="form-field form-grid-wide"><label htmlFor="supplier-complement">Complemento (opcional)</label><input id="supplier-complement" value={form.complemento ?? ''} onChange={(event) => updateField('complemento', event.target.value)} /></div>
    <CustomFieldFields module="suppliers" values={customValues} onChange={(name, value) => setCustomValues((current) => ({ ...current, [name]: value }))} />
  </div><div className="form-actions"><button className="button button-secondary" type="button" onClick={onCancel} disabled={saving}>Cancelar</button><button className="button button-primary" type="submit" disabled={saving}>{saving ? 'Salvando...' : 'Salvar fornecedor'}</button></div></form>
}

function SupplierDetails({ supplier }: { supplier: SupplierDetails }) {
  return <><dl className="detail-grid"><div><dt>Nome</dt><dd>{supplier.nome}</dd></div><div><dt>CNPJ</dt><dd>{supplier.cnpj}</dd></div><div><dt>Cidade / Estado</dt><dd>{supplier.cidade} / {supplier.estado}</dd></div><div><dt>Rua</dt><dd>{supplier.rua}, {supplier.numero}</dd></div><div className="form-grid-wide"><dt>Complemento</dt><dd>{supplier.complemento || 'Não informado'}</dd></div></dl><CustomFieldDetails values={supplier.campos_personalizados} /><section className="relational-detail-section" aria-labelledby="supplier-products-title"><div className="relational-detail-heading"><h3 id="supplier-products-title">Produtos fornecidos</h3><span>{supplier.produtos.length} {supplier.produtos.length === 1 ? 'produto' : 'produtos'}</span></div>{supplier.produtos.length === 0 ? <p className="relational-detail-empty">Nenhum produto associado a este fornecedor.</p> : <ul className="relational-detail-list">{supplier.produtos.map((product) => <li className="relational-detail-item" key={product.id}><strong>{product.nome}</strong></li>)}</ul>}</section></>
}

export function SuppliersPage() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [filterSuppliers, setFilterSuppliers] = useState<Supplier[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchDraft, setSearchDraft] = useState('')
  const [cityDraft, setCityDraft] = useState('')
  const [stateDraft, setStateDraft] = useState('')
  const [appliedFilters, setAppliedFilters] = useState<SupplierListFilters>({})
  const [page, setPage] = useState(1)
  const [pagination, setPagination] = useState<PaginationMeta>({ page: 1, page_size: PAGE_SIZE, total: 0, total_pages: 0 })
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [feedback, setFeedback] = useState<{ kind: 'success' | 'error'; message: string } | null>(null)
  const [modal, setModal] = useState<'create' | 'edit' | 'view' | null>(null)
  const [selected, setSelected] = useState<Supplier | null>(null)
  const [selectedDetails, setSelectedDetails] = useState<SupplierDetails | null>(null)
  const [detailsLoading, setDetailsLoading] = useState(false)
  const [detailsError, setDetailsError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<Supplier | null>(null)
  const createButtonCustomization = useCustomizable({ key: 'suppliers.create_button', type: 'BUTTON', group: 'primary-action', page: 'suppliers', label: 'Novo fornecedor' })
  const tableCustomization = useCustomizable({ key: 'suppliers.table', type: 'TABLE', group: 'data-table', page: 'suppliers', label: 'Tabela de fornecedores' })
  const [deleting, setDeleting] = useState(false)
  const loadRequestId = useRef(0)

  const loadSuppliers = useCallback(async () => { const requestId = ++loadRequestId.current; setLoading(true); setError(null); try { const [supplierList, optionList] = await Promise.all([listSuppliers({ ...appliedFilters, page, pageSize: PAGE_SIZE }), listSuppliers({ page: 1, pageSize: 100 })]); if (requestId !== loadRequestId.current) return; setSuppliers(supplierList); setFilterSuppliers(optionList); setPagination(getPaginationMeta(supplierList)) } catch (loadError) { if (requestId === loadRequestId.current) setError(getApiErrorMessage(loadError, 'Não foi possível carregar os fornecedores.')) } finally { if (requestId === loadRequestId.current) setLoading(false) } }, [appliedFilters, page])
  // oxlint-disable-next-line
  useEffect(() => { void loadSuppliers() }, [loadSuppliers])

  const hasDraftFilters = Boolean(searchDraft.trim() || cityDraft || stateDraft)
  const filterCities = useMemo(() => uniqueFilterOptions(filterSuppliers.map((supplier) => supplier.cidade)), [filterSuppliers])
  const filterStates = useMemo(() => uniqueFilterOptions(filterSuppliers.map((supplier) => supplier.estado)), [filterSuppliers])
  const activeFilters: ActiveFilterItem[] = [
    appliedFilters.search ? { key: 'search', label: 'Busca', value: appliedFilters.search } : null,
    appliedFilters.city ? { key: 'city', label: 'Cidade', value: appliedFilters.city } : null,
    appliedFilters.state ? { key: 'state', label: 'Estado', value: appliedFilters.state } : null,
  ].filter((filter): filter is ActiveFilterItem => filter !== null)
  const hasAppliedFilters = activeFilters.length > 0
  const applyFilters = () => { setPage(1); setAppliedFilters({ search: searchDraft.trim(), city: cityDraft, state: stateDraft }); setFiltersOpen(false) }
  const clearFilters = () => { setPage(1); setSearchDraft(''); setCityDraft(''); setStateDraft(''); setAppliedFilters({}); setFiltersOpen(false) }
  const removeFilter = (key: string) => {
    setPage(1)
    if (key === 'search') setSearchDraft('')
    if (key === 'city') setCityDraft('')
    if (key === 'state') setStateDraft('')
    setAppliedFilters((current) => {
      const next = { ...current }
      delete next[key as SupplierFilterKey]
      return next
    })
  }

  const openSupplierDetails = async (supplier: Supplier) => {
    setSelected(supplier)
    setSelectedDetails(null)
    setDetailsError(null)
    setDetailsLoading(true)
    setModal('view')
    try {
      setSelectedDetails(await getSupplier(supplier.id))
    } catch (loadError) {
      setDetailsError(getApiErrorMessage(loadError, 'Não foi possível carregar os detalhes do fornecedor.'))
    } finally {
      setDetailsLoading(false)
    }
  }

  const saveSupplier = async (payload: SupplierPayload) => {
    setSaving(true); setFeedback(null)
    try { const saved = selected ? await updateSupplier(selected.id, payload) : await createSupplier(payload); setSuppliers((current) => selected ? current.map((item) => item.id === saved.id ? saved : item) : [...current, saved]); setFilterSuppliers((current) => selected ? current.map((item) => item.id === saved.id ? saved : item) : [...current, saved]); setModal(null); setSelected(null); setFeedback({ kind: 'success', message: selected ? 'Fornecedor atualizado com sucesso.' : 'Fornecedor criado com sucesso.' }) } catch (saveError) { setFeedback({ kind: 'error', message: getApiErrorMessage(saveError, 'Não foi possível salvar o fornecedor.') }) } finally { setSaving(false) }
  }

  const removeSupplier = async () => {
    if (!deleteTarget) return
    setDeleting(true); setFeedback(null)
    try { await deleteSupplier(deleteTarget.id); setSuppliers((current) => current.filter((item) => item.id !== deleteTarget.id)); setFilterSuppliers((current) => current.filter((item) => item.id !== deleteTarget.id)); setFeedback({ kind: 'success', message: 'Fornecedor excluído com sucesso.' }) } catch (deleteError) { setFeedback({ kind: 'error', message: getApiErrorMessage(deleteError, 'Não é possível excluir este fornecedor porque há produtos relacionados.') }) } finally { setDeleting(false); setDeleteTarget(null) }
  }

  const formValue: SupplierPayload = selected
    ? (({ id: _id, campos_personalizados: _custom, ...payload }) => payload)(selected)
    : emptySupplier
  return <div className="crud-page cadastros-family-page suppliers-page">
    <div className="crud-page-header"><PageHeader eyebrow="Cadastros" title="Fornecedores" description="Mantenha os parceiros do seu negócio organizados." pageId="suppliers" /><button className="button button-primary" type="button" {...createButtonCustomization} onClick={() => { setSelected(null); setModal('create'); setFeedback(null) }}>+ Novo fornecedor</button></div>
      {feedback ? <FeedbackBanner kind={feedback.kind} message={feedback.message} onDismiss={() => setFeedback(null)} /> : null}
      <section className="filter-toolbar cadastros-filter-toolbar" aria-label="Filtros de fornecedores">
        <SearchInput value={searchDraft} onChange={setSearchDraft} onSearch={(value) => { setPage(1); setAppliedFilters((current) => { const search = value.trim(); if (current.search === search) return current; const { search: _search, ...filters } = current; return search ? { ...filters, search } : filters }) }} onClear={() => setSearchDraft('')} label="Pesquisar fornecedores" customizationKey="suppliers.search_input" customizationPage="suppliers" />
        <FilterMenu activeCount={activeFilters.length} canClear={hasDraftFilters || hasAppliedFilters} open={filtersOpen} onToggle={() => setFiltersOpen((current) => !current)} onClose={() => setFiltersOpen(false)} onApply={applyFilters} onClear={clearFilters}>
          <label className="filter-field">Cidade<select value={cityDraft} onChange={(event) => setCityDraft(event.target.value)}><option value="">Todas as cidades</option>{filterCities.map((city) => <option value={city} key={city}>{city}</option>)}</select></label>
          <label className="filter-field">Estado<select value={stateDraft} onChange={(event) => setStateDraft(event.target.value)}><option value="">Todos os estados</option>{filterStates.map((state) => <option value={state} key={state}>{state}</option>)}</select></label>
        </FilterMenu>
      </section>
    <ActiveFilters filters={activeFilters} onRemove={removeFilter} onClear={clearFilters} />
    {loading ? <CadastrosListLoading label="Carregando fornecedores..." /> : error ? <ErrorState description={error} onRetry={() => void loadSuppliers()} /> : suppliers.length === 0 ? <div className="data-card cadastros-empty-state"><EmptyState title={hasAppliedFilters ? 'Nenhum resultado encontrado para os filtros aplicados.' : 'Nenhum fornecedor cadastrado ainda'} description={hasAppliedFilters ? 'Ajuste a busca ou remova os filtros ativos para ver outros fornecedores.' : 'Crie o primeiro fornecedor usando a ação Novo fornecedor acima.'} /></div> : <><div className="data-card data-table-wrap cadastros-table suppliers-table"><table className="data-table" {...tableCustomization}><thead><tr><th>Fornecedor</th><th>CNPJ</th><th>Localização</th><th><span className="sr-only">Ações</span></th></tr></thead><tbody>{suppliers.map((supplier) => <tr key={supplier.id}><td className="data-primary">{supplier.nome}<span className="data-secondary">ID {supplier.id}</span></td><td>{supplier.cnpj}</td><td>{supplier.cidade} / {supplier.estado}</td><td><div className="table-actions"><button className="table-action" type="button" onClick={() => void openSupplierDetails(supplier)}>Ver</button><button className="table-action" type="button" onClick={() => { setSelected(supplier); setModal('edit') }}>Editar</button><button className="table-action table-action-danger" type="button" onClick={() => setDeleteTarget(supplier)}>Excluir</button></div></td></tr>)}</tbody></table></div><PaginationControls meta={pagination} onPageChange={setPage} /></>}
    {modal === 'view' && selected ? <Modal title="Detalhes do fornecedor" size="large" onClose={() => { setModal(null); setSelectedDetails(null) }}>{detailsLoading ? <LoadingState label="Carregando detalhes do fornecedor..." /> : detailsError ? <ErrorState description={detailsError} onRetry={() => void openSupplierDetails(selected)} /> : selectedDetails ? <SupplierDetails supplier={selectedDetails} /> : null}</Modal> : null}
    {(modal === 'create' || modal === 'edit') ? <Modal title={modal === 'edit' ? 'Editar fornecedor' : 'Novo fornecedor'} description="O CNPJ é obrigatório e deve ser único." onClose={() => setModal(null)}><SupplierForm initialValue={formValue} saving={saving} onCancel={() => setModal(null)} onSave={(payload) => void saveSupplier(payload)} /></Modal> : null}
    {deleteTarget ? <ConfirmDialog title="Excluir fornecedor?" description={`O cadastro de ${deleteTarget.nome} será removido. Produtos relacionados impedem a exclusão.`} busy={deleting} onCancel={() => setDeleteTarget(null)} onConfirm={() => void removeSupplier()} /> : null}
  </div>
}
