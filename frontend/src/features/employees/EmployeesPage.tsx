import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from 'react'

import { ConfirmDialog } from '../../components/ConfirmDialog'
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
import { createEmployee, deleteEmployee, getEmployee, listEmployees, updateEmployee } from './api'
import type { Employee, EmployeePayload } from './types'

const emptyEmployee: EmployeePayload = { nome_completo: '', cidade: '', estado: '', rua: '', numero: '', complemento: '', cpf: '', rg: '', data_nascimento: '' }
const PAGE_SIZE = 20

function EmployeeForm({ initialValue, saving, onCancel, onSave }: { initialValue: EmployeePayload; saving: boolean; onCancel: () => void; onSave: (payload: EmployeePayload) => void }) {
  const [form, setForm] = useState({ ...initialValue, complemento: initialValue.complemento ?? '', rg: initialValue.rg ?? '' })
  const [customValues, setCustomValues] = useState<Record<string, unknown>>({})
  const updateField = (field: keyof Omit<EmployeePayload, 'ativo'>, value: string) => setForm((current) => ({ ...current, [field]: value }))
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const { ativo, ...fields } = form
    const payload = { ...fields, complemento: form.complemento.trim() || null, rg: form.rg.trim() || null }
    const customPayload = Object.keys(customValues).length ? { campos_personalizados: customValues } : {}
    onSave(initialValue.ativo === undefined ? { ...payload, ...customPayload } : { ...payload, ativo: ativo ?? true, ...customPayload })
  }

  return <form onSubmit={submit}><div className="form-grid">
    <div className="form-field form-grid-wide"><label htmlFor="employee-name">Nome completo</label><input id="employee-name" required value={form.nome_completo} onChange={(event) => updateField('nome_completo', event.target.value)} /></div>
    <div className="form-field"><label htmlFor="employee-cpf">CPF</label><input id="employee-cpf" required value={form.cpf} onChange={(event) => updateField('cpf', event.target.value)} /></div>
    <div className="form-field"><label htmlFor="employee-rg">RG (opcional)</label><input id="employee-rg" value={form.rg} onChange={(event) => updateField('rg', event.target.value)} /></div>
    <div className="form-field"><label htmlFor="employee-birth">Data de nascimento</label><input id="employee-birth" required type="date" value={form.data_nascimento} onChange={(event) => updateField('data_nascimento', event.target.value)} /></div>
    <div className="form-field"><label htmlFor="employee-city">Cidade</label><input id="employee-city" required value={form.cidade} onChange={(event) => updateField('cidade', event.target.value)} /></div>
    <div className="form-field"><label htmlFor="employee-state">Estado</label><input id="employee-state" required maxLength={2} value={form.estado} onChange={(event) => updateField('estado', event.target.value.toUpperCase())} /></div>
    <div className="form-field"><label htmlFor="employee-street">Rua</label><input id="employee-street" required value={form.rua} onChange={(event) => updateField('rua', event.target.value)} /></div>
    <div className="form-field"><label htmlFor="employee-number">Número</label><input id="employee-number" required value={form.numero} onChange={(event) => updateField('numero', event.target.value)} /></div>
    <div className="form-field form-grid-wide"><label htmlFor="employee-complement">Complemento (opcional)</label><input id="employee-complement" value={form.complemento} onChange={(event) => updateField('complemento', event.target.value)} /></div>
    {initialValue.ativo !== undefined ? <div className="form-field"><label htmlFor="employee-status">Status</label><select id="employee-status" value={form.ativo ? 'active' : 'inactive'} onChange={(event) => setForm((current) => ({ ...current, ativo: event.target.value === 'active' }))}><option value="active">Ativo</option><option value="inactive">Inativo</option></select><span className="form-help">Funcionários inativos não aparecem em novas vendas.</span></div> : null}
    <CustomFieldFields module="employees" values={customValues} onChange={(name, value) => setCustomValues((current) => ({ ...current, [name]: value }))} />
  </div><div className="form-actions"><button className="button button-secondary" type="button" onClick={onCancel} disabled={saving}>Cancelar</button><button className="button button-primary" type="submit" disabled={saving}>{saving ? 'Salvando...' : 'Salvar funcionário'}</button></div></form>
}

function EmployeeDetails({ employee }: { employee: Employee }) {
  return <><dl className="detail-grid"><div><dt>Nome completo</dt><dd>{employee.nome_completo}</dd></div><div><dt>Status</dt><dd><span className={`status-badge ${employee.ativo ? 'status-badge-active' : 'status-badge-inactive'}`}>{employee.ativo ? 'Ativo' : 'Inativo'}</span></dd></div><div><dt>CPF</dt><dd>{employee.cpf}</dd></div><div><dt>RG</dt><dd>{employee.rg || 'Não informado'}</dd></div><div><dt>Nascimento</dt><dd>{employee.data_nascimento}</dd></div><div><dt>Localização</dt><dd>{employee.cidade} / {employee.estado}</dd></div><div><dt>Endereço</dt><dd>{employee.rua}, {employee.numero}</dd></div><div className="form-grid-wide"><dt>Complemento</dt><dd>{employee.complemento || 'Não informado'}</dd></div></dl><CustomFieldDetails values={employee.campos_personalizados} /></>
}

export function EmployeesPage() {
  const [employees, setEmployees] = useState<Employee[]>([])
  const [filterEmployees, setFilterEmployees] = useState<Employee[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchDraft, setSearchDraft] = useState('')
  const [appliedSearch, setAppliedSearch] = useState('')
  const [cityDraft, setCityDraft] = useState('')
  const [stateDraft, setStateDraft] = useState('')
  const [statusDraft, setStatusDraft] = useState<'all' | 'active' | 'inactive'>('all')
  const [appliedCity, setAppliedCity] = useState('')
  const [appliedState, setAppliedState] = useState('')
  const [appliedStatus, setAppliedStatus] = useState<'all' | 'active' | 'inactive'>('all')
  const [page, setPage] = useState(1)
  const [pagination, setPagination] = useState<PaginationMeta>({ page: 1, page_size: PAGE_SIZE, total: 0, total_pages: 0 })
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [feedback, setFeedback] = useState<{ kind: 'success' | 'error'; message: string } | null>(null)
  const [modal, setModal] = useState<'create' | 'edit' | 'view' | null>(null)
  const [selected, setSelected] = useState<Employee | null>(null)
  const [selectedDetails, setSelectedDetails] = useState<Employee | null>(null)
  const [detailsLoading, setDetailsLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<Employee | null>(null)
  const createButtonCustomization = useCustomizable({ key: 'employees.create_button', type: 'BUTTON', group: 'primary-action', page: 'employees', label: 'Novo funcionário' })
  const tableCustomization = useCustomizable({ key: 'employees.table', type: 'TABLE', group: 'data-table', page: 'employees', label: 'Tabela de funcionários' })
  const [deleting, setDeleting] = useState(false)
  const loadRequestId = useRef(0)

  const loadEmployees = useCallback(async () => {
    const requestId = ++loadRequestId.current
    setLoading(true)
    setError(null)
    const active = appliedStatus === 'all' ? undefined : appliedStatus === 'active'
    const options = { active, city: appliedCity, state: appliedState, page, pageSize: PAGE_SIZE }
    try {
      const employeesRequest = listEmployees(active === true, appliedSearch, options)
      const [employeeList, optionList] = await Promise.all([employeesRequest, listEmployees(false, '', { page: 1, pageSize: 100 })])
      if (requestId !== loadRequestId.current) return
      setEmployees(employeeList)
      setFilterEmployees(optionList)
      setPagination(getPaginationMeta(employeeList))
    } catch (loadError) { if (requestId === loadRequestId.current) setError(getApiErrorMessage(loadError, 'Não foi possível carregar os funcionários.')) } finally { if (requestId === loadRequestId.current) setLoading(false) }
  }, [appliedCity, appliedSearch, appliedState, appliedStatus, page])

  // oxlint-disable-next-line
  useEffect(() => { void loadEmployees() }, [loadEmployees])

  const hasDraftFilters = Boolean(searchDraft.trim() || cityDraft || stateDraft || statusDraft !== 'all')
  const hasAppliedFilters = Boolean(appliedSearch || appliedCity || appliedState || appliedStatus !== 'all')
  const filterCities = useMemo(() => uniqueFilterOptions(filterEmployees.map((employee) => employee.cidade)), [filterEmployees])
  const filterStates = useMemo(() => uniqueFilterOptions(filterEmployees.map((employee) => employee.estado)), [filterEmployees])
  const applyFilters = () => { setPage(1); setAppliedSearch(searchDraft.trim()); setAppliedCity(cityDraft); setAppliedState(stateDraft); setAppliedStatus(statusDraft); setFiltersOpen(false) }
  const clearFilters = () => { setPage(1); setSearchDraft(''); setAppliedSearch(''); setCityDraft(''); setAppliedCity(''); setStateDraft(''); setAppliedState(''); setStatusDraft('all'); setAppliedStatus('all'); setFiltersOpen(false) }

  const saveEmployee = async (payload: EmployeePayload) => {
    setSaving(true); setFeedback(null)
    try { const saved = selected ? await updateEmployee(selected.id, payload) : await createEmployee(payload); setEmployees((current) => selected ? current.map((item) => item.id === saved.id ? saved : item) : [...current, saved]); setFilterEmployees((current) => selected ? current.map((item) => item.id === saved.id ? saved : item) : [...current, saved]); setModal(null); setSelected(null); setFeedback({ kind: 'success', message: selected ? 'Funcionário atualizado com sucesso.' : 'Funcionário criado com sucesso.' }) } catch (saveError) { setFeedback({ kind: 'error', message: getApiErrorMessage(saveError, 'Não foi possível salvar o funcionário.') }) } finally { setSaving(false) }
  }

  const removeEmployee = async () => {
    if (!deleteTarget) return
    setDeleting(true); setFeedback(null)
    try { await deleteEmployee(deleteTarget.id); setEmployees((current) => current.filter((item) => item.id !== deleteTarget.id)); setFilterEmployees((current) => current.filter((item) => item.id !== deleteTarget.id)); setFeedback({ kind: 'success', message: 'Funcionário excluído com sucesso.' }) } catch (deleteError) { setFeedback({ kind: 'error', message: getApiErrorMessage(deleteError, 'Não é possível excluir este funcionário porque há vendas relacionadas.') }) } finally { setDeleting(false); setDeleteTarget(null) }
  }

  const openEmployeeDetails = async (employee: Employee) => {
    setSelected(employee)
    setSelectedDetails(null)
    setDetailsLoading(true)
    setModal('view')
    try {
      setSelectedDetails(await getEmployee(employee.id))
    } catch (error) {
      setFeedback({ kind: 'error', message: getApiErrorMessage(error, 'Não foi possível carregar os detalhes do funcionário.') })
    } finally {
      setDetailsLoading(false)
    }
  }

  const formValue: EmployeePayload = selected ? (({ id: _id, campos_personalizados: _custom, ...payload }) => payload)(selected) : emptyEmployee

  return <div className="crud-page">
    <div className="crud-page-header"><PageHeader eyebrow="Cadastros" title="Funcionários" description="Organize a equipe que participa da operação." pageId="employees" /><button className="button button-primary" type="button" {...createButtonCustomization} onClick={() => { setSelected(null); setModal('create'); setFeedback(null) }}>+ Novo funcionário</button></div>
      {feedback ? <FeedbackBanner kind={feedback.kind} message={feedback.message} onDismiss={() => setFeedback(null)} /> : null}
      <section className="filter-toolbar" aria-label="Filtros de funcionários">
        <SearchInput value={searchDraft} onChange={setSearchDraft} onSearch={(value) => { const search = value.trim(); setAppliedSearch((current) => current === search ? current : search) }} onClear={() => setSearchDraft('')} label="Pesquisar funcionários" customizationKey="employees.search_input" customizationPage="employees" />
        <FilterMenu activeCount={[appliedCity, appliedState, appliedStatus !== 'all' ? appliedStatus : ''].filter(Boolean).length} canClear={hasDraftFilters || hasAppliedFilters} open={filtersOpen} onToggle={() => setFiltersOpen((current) => !current)} onClose={() => setFiltersOpen(false)} onApply={applyFilters} onClear={clearFilters}>
          <label className="filter-field">Cidade<select value={cityDraft} onChange={(event) => setCityDraft(event.target.value)}><option value="">Todas as cidades</option>{filterCities.map((city) => <option value={city} key={city}>{city}</option>)}</select></label>
          <label className="filter-field">Estado<select value={stateDraft} onChange={(event) => setStateDraft(event.target.value)}><option value="">Todos os estados</option>{filterStates.map((state) => <option value={state} key={state}>{state}</option>)}</select></label>
          <label className="filter-field">Status<select value={statusDraft} onChange={(event) => setStatusDraft(event.target.value as 'all' | 'active' | 'inactive')}><option value="all">Todos</option><option value="active">Ativos</option><option value="inactive">Inativos</option></select></label>
        </FilterMenu>
      </section>
      {loading ? <LoadingState label="Carregando funcionários..." /> : error ? <ErrorState description={error} onRetry={() => void loadEmployees()} /> : employees.length === 0 ? <div className="data-card"><EmptyState title={hasAppliedFilters ? 'Nenhum resultado encontrado para os filtros aplicados.' : 'Nenhum funcionário cadastrado ainda'} description={hasAppliedFilters ? 'Tente ajustar a pesquisa ou limpar os filtros.' : 'Crie o primeiro funcionário responsável pela operação.'} /></div> : <><div className="data-card data-table-wrap"><table className="data-table" {...tableCustomization}><thead><tr><th>Funcionário</th><th>Status</th><th>CPF</th><th>Localização</th><th><span className="sr-only">Ações</span></th></tr></thead><tbody>{employees.map((employee) => <tr key={employee.id}><td className="data-primary">{employee.nome_completo}<span className="data-secondary">ID {employee.id}</span></td><td><span className={`status-badge ${employee.ativo ? 'status-badge-active' : 'status-badge-inactive'}`}>{employee.ativo ? 'Ativo' : 'Inativo'}</span></td><td>{employee.cpf}</td><td>{employee.cidade} / {employee.estado}</td><td><div className="table-actions"><button className="table-action" type="button" onClick={() => void openEmployeeDetails(employee)}>Ver</button><button className="table-action" type="button" onClick={() => { setSelected(employee); setModal('edit') }}>Editar</button><button className="table-action table-action-danger" type="button" onClick={() => setDeleteTarget(employee)}>Excluir</button></div></td></tr>)}</tbody></table></div><PaginationControls meta={pagination} onPageChange={setPage} /></>}
    {modal === 'view' && selected ? <Modal title="Detalhes do funcionário" onClose={() => { setModal(null); setSelectedDetails(null) }}>{detailsLoading ? <LoadingState label="Carregando detalhes do funcionário..." /> : selectedDetails ? <EmployeeDetails employee={selectedDetails} /> : null}</Modal> : null}
    {(modal === 'create' || modal === 'edit') ? <Modal title={modal === 'edit' ? 'Editar funcionário' : 'Novo funcionário'} description="RG e complemento são opcionais." onClose={() => setModal(null)}><EmployeeForm initialValue={formValue} saving={saving} onCancel={() => setModal(null)} onSave={(payload) => void saveEmployee(payload)} /></Modal> : null}
    {deleteTarget ? <ConfirmDialog title="Excluir funcionário?" description={`O cadastro de ${deleteTarget.nome_completo} será removido. Vendas relacionadas impedem a exclusão.`} busy={deleting} onCancel={() => setDeleteTarget(null)} onConfirm={() => void removeEmployee()} /> : null}
  </div>
}
