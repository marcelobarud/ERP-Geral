import { useEffect, useMemo, useState, type FormEvent } from 'react'

import { EmptyState } from '../../components/EmptyState'
import { ErrorState } from '../../components/ErrorState'
import { FeedbackBanner } from '../../components/FeedbackBanner'
import { LoadingState } from '../../components/LoadingState'
import { Modal } from '../../components/Modal'
import { PageHeader } from '../../components/PageHeader'
import { getApiErrorMessage } from '../../services/httpClient'
import { listCustomers } from '../customers/api'
import type { Customer } from '../customers/types'
import { listEmployees } from '../employees/api'
import type { Employee } from '../employees/types'
import { listProducts } from '../products/api'
import type { Product } from '../products/types'
import { listSales } from '../sales/api'
import type { Sale } from '../sales/types'
import { useCustomizable } from '../settings/VisualCustomizationContext'
import * as api from './api'
import type { CommercialDocumentBase, CommercialDocumentPayload, Order, OrderStatus, PaymentCondition, Quote, QuoteStatus, SaleReturn } from './types'

type DocumentKind = 'quote' | 'order'
type ItemDraft = { produto_id: number | ''; quantidade: string; preco_unitario: string }

function money(value: string | number): string {
  return `R$ ${Number(value).toFixed(2).replace('.', ',')}`
}

function statusLabel(status: string): string {
  return status.replace('CONCLUIDO', 'CONCLUÍDO').replace('APROVADO', 'APROVADO').replace('ENVIADO', 'ENVIADO').replace('RASCUNHO', 'RASCUNHO').replace('CONFIRMADO', 'CONFIRMADO').replace('CANCELADO', 'CANCELADO').replace('RECUSADO', 'RECUSADO').replace('EXPIRADO', 'EXPIRADO')
}

function nextStatuses(kind: DocumentKind, status: string): string[] {
  if (kind === 'quote') return status === 'RASCUNHO' ? ['ENVIADO', 'CANCELADO'] : status === 'ENVIADO' ? ['APROVADO', 'RECUSADO', 'EXPIRADO', 'CANCELADO'] : status === 'APROVADO' ? ['CANCELADO'] : []
  return status === 'RASCUNHO' ? ['CONFIRMADO', 'CANCELADO'] : status === 'CONFIRMADO' ? ['CONCLUIDO', 'CANCELADO'] : status === 'CONCLUIDO' ? ['CANCELADO'] : []
}

function documentTitle(kind: DocumentKind): string { return kind === 'quote' ? 'Orçamentos' : 'Pedidos de venda' }

function DocumentForm({ kind, document, onSaved, onCancel }: { kind: DocumentKind; document?: CommercialDocumentBase; onSaved: (saved: CommercialDocumentBase) => void; onCancel: () => void }) {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [employees, setEmployees] = useState<Employee[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [conditions, setConditions] = useState<PaymentCondition[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [numero, setNumero] = useState(document?.numero ?? '')
  const [clienteId, setClienteId] = useState<number | ''>(document?.cliente_id ?? '')
  const [funcionarioId, setFuncionarioId] = useState<number | ''>(document?.funcionario_id ?? '')
  const [conditionId, setConditionId] = useState<number | ''>(document?.condicao_pagamento_id ?? '')
  const quoteDocument = document as Quote | undefined
  const [validade, setValidade] = useState(quoteDocument?.validade ? String(quoteDocument.validade) : '')
  const [observacao, setObservacao] = useState(document?.observacao ?? '')
  const [items, setItems] = useState<ItemDraft[]>(document?.itens.map((item) => ({ produto_id: item.produto_id, quantidade: String(item.quantidade), preco_unitario: String(item.preco_unitario) })) ?? [{ produto_id: '', quantidade: '1', preco_unitario: '' }])

  useEffect(() => {
    Promise.all([listCustomers({ page: 1, pageSize: 100 }), listEmployees(true, '', { page: 1, pageSize: 100 }), listProducts({ page: 1, pageSize: 100 }), api.listPaymentConditions()])
      .then(([customerList, employeeList, productList, conditionList]) => { setCustomers(customerList); setEmployees(employeeList); setProducts(productList); setConditions(conditionList) })
      .catch((loadError) => setError(getApiErrorMessage(loadError, 'Não foi possível carregar as opções comerciais.')))
      .finally(() => setLoading(false))
  }, [])

  const updateItem = (index: number, patch: Partial<ItemDraft>) => setItems((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, ...patch } : item))
  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (!clienteId || items.some((item) => !item.produto_id || !item.quantidade)) { setError('Informe cliente e itens válidos para continuar.'); return }
    setSaving(true); setError(null)
    const payload: CommercialDocumentPayload = {
      numero: numero.trim() || undefined,
      cliente_id: clienteId,
      funcionario_id: funcionarioId || null,
      condicao_pagamento_id: conditionId || null,
      validade: kind === 'quote' ? validade || null : undefined,
      observacao: observacao.trim() || null,
      itens: items.map((item) => ({ produto_id: Number(item.produto_id), quantidade: item.quantidade, preco_unitario: item.preco_unitario || undefined })),
    }
    try {
      const saved = document ? kind === 'quote' ? await api.updateQuote(document.id, payload) : await api.updateOrder(document.id, payload) : kind === 'quote' ? await api.createQuote(payload) : await api.createOrder(payload)
      onSaved(saved)
    } catch (saveError) { setError(getApiErrorMessage(saveError, 'Não foi possível salvar o documento.')) } finally { setSaving(false) }
  }

  if (loading) return <LoadingState label="Carregando opções comerciais..." />
  if (error && customers.length === 0) return <ErrorState description={error} />
  return <form onSubmit={submit}>
    {error ? <FeedbackBanner kind="error" message={error} /> : null}
    <div className="form-grid">
      <label className="form-field"><span>Número (opcional)</span><input value={numero} onChange={(event) => setNumero(event.target.value)} /></label>
      <label className="form-field"><span>Cliente</span><select required value={clienteId} onChange={(event) => setClienteId(Number(event.target.value) || '')}><option value="">Selecione</option>{customers.map((customer) => <option value={customer.id} key={customer.id}>{customer.nome}</option>)}</select></label>
      <label className="form-field"><span>Funcionário</span><select value={funcionarioId} onChange={(event) => setFuncionarioId(Number(event.target.value) || '')}><option value="">Não informado</option>{employees.map((employee) => <option value={employee.id} key={employee.id}>{employee.nome_completo}</option>)}</select></label>
      <label className="form-field"><span>Condição de pagamento</span><select value={conditionId} onChange={(event) => setConditionId(Number(event.target.value) || '')}><option value="">Não informado</option>{conditions.map((condition) => <option value={condition.id} key={condition.id}>{condition.nome}</option>)}</select></label>
      {kind === 'quote' ? <label className="form-field"><span>Validade</span><input type="date" value={validade} onChange={(event) => setValidade(event.target.value)} /></label> : null}
      <label className="form-field form-grid-wide"><span>Observação</span><textarea maxLength={1000} value={observacao} onChange={(event) => setObservacao(event.target.value)} /></label>
    </div>
    <h3>Itens</h3>
    {items.map((item, index) => <div className="form-grid" key={index}>
      <label className="form-field"><span>Produto</span><select required value={item.produto_id} onChange={(event) => updateItem(index, { produto_id: Number(event.target.value) || '', preco_unitario: products.find((product) => product.id === Number(event.target.value))?.preco_venda?.toString() ?? '' })}><option value="">Selecione</option>{products.map((product) => <option value={product.id} key={product.id}>{product.nome} · {money(product.preco_venda)}</option>)}</select></label>
      <label className="form-field"><span>Quantidade</span><input required min="0.001" step="0.001" type="number" value={item.quantidade} onChange={(event) => updateItem(index, { quantidade: event.target.value })} /></label>
      <label className="form-field"><span>Preço unitário</span><input min="0" step="0.01" type="number" value={item.preco_unitario} onChange={(event) => updateItem(index, { preco_unitario: event.target.value })} /></label>
      {items.length > 1 ? <button className="table-action table-action-danger" type="button" onClick={() => setItems((current) => current.filter((_, itemIndex) => itemIndex !== index))}>Remover</button> : null}
    </div>)}
    <button className="button button-secondary" type="button" onClick={() => setItems((current) => [...current, { produto_id: '', quantidade: '1', preco_unitario: '' }])}>+ Adicionar item</button>
    <div className="form-actions"><button className="button button-secondary" type="button" onClick={onCancel}>Cancelar</button><button className="button button-primary" type="submit" disabled={saving}>{saving ? 'Salvando...' : 'Salvar documento'}</button></div>
  </form>
}

function DocumentDetails({ document, kind, customerName, onStatus, onConvert }: { document: CommercialDocumentBase; kind: DocumentKind; customerName: (id: number) => string; onStatus: (status: string) => void; onConvert: () => void }) {
  const transitions = nextStatuses(kind, document.status)
  return <div>
    <dl className="detail-grid"><div><dt>Número</dt><dd>{document.numero}</dd></div><div><dt>Cliente</dt><dd>{customerName(document.cliente_id)}</dd></div><div><dt>Status</dt><dd>{statusLabel(document.status)}</dd></div><div><dt>Total</dt><dd>{money(document.total)}</dd></div><div><dt>Origem</dt><dd>{'orcamento_id' in document && document.orcamento_id ? `Orçamento #${document.orcamento_id}` : 'Sem origem'}</dd></div><div><dt>Condição de pagamento</dt><dd>{document.condicao_pagamento_id ? `#${document.condicao_pagamento_id}` : 'Não informada'}</dd></div></dl>
    {document.observacao ? <p><strong>Observação:</strong> {document.observacao}</p> : null}
    <div className="data-card data-table-wrap"><table className="data-table"><thead><tr><th>Produto</th><th>Quantidade</th><th>Unitário</th><th>Total</th></tr></thead><tbody>{document.itens.map((item) => <tr key={item.id}><td>{item.produto_nome}</td><td>{item.quantidade}</td><td>{money(item.preco_unitario)}</td><td>{money(item.total)}</td></tr>)}</tbody></table></div>
    <div className="form-actions">{transitions.map((status) => <button className="button button-secondary" type="button" key={status} onClick={() => onStatus(status)}>{statusLabel(status)}</button>)}{kind === 'quote' && document.status === 'APROVADO' && !('pedido_id' in document && document.pedido_id) ? <button className="button button-primary" type="button" onClick={onConvert}>Converter em pedido</button> : null}{kind === 'order' && ['CONFIRMADO', 'CONCLUIDO'].includes(document.status) && !('venda_id' in document && document.venda_id) ? <button className="button button-primary" type="button" onClick={onConvert}>Converter em venda</button> : null}</div>
  </div>
}

function CommercialListPage({ kind }: { kind: DocumentKind }) {
  const [documents, setDocuments] = useState<(Quote | Order)[]>([])
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [selected, setSelected] = useState<(Quote | Order) | null>(null)
  const [editing, setEditing] = useState<(Quote | Order) | 'create' | null>(null)
  const tableCustomization = useCustomizable({ key: `commercial.${kind}.table`, type: 'TABLE', group: 'data-table', page: 'settings', label: documentTitle(kind) })
  const customerName = (customerId: number) => customers.find((customer) => customer.id === customerId)?.nome ?? `Cliente #${customerId}`
  const load = () => { (kind === 'quote' ? api.listQuotes({ search, status: status as QuoteStatus || undefined }) : api.listOrders({ search, status: status as OrderStatus || undefined })).then(setDocuments).catch((loadError) => setError(getApiErrorMessage(loadError, 'Não foi possível carregar os documentos.'))).finally(() => setLoading(false)) }
  // oxlint-disable-next-line
  useEffect(load, [kind, search, status])
  useEffect(() => { void listCustomers({ page: 1, pageSize: 100 }).then(setCustomers).catch(() => setCustomers([])) }, [])
  const isQuote = kind === 'quote'
  const canEdit = (document: CommercialDocumentBase) => document.status === 'RASCUNHO' && (!('pedido_id' in document) || !document.pedido_id) && (!('venda_id' in document) || !document.venda_id)
  const saved = (document: CommercialDocumentBase) => { setDocuments((current) => editing === 'create' ? [document as Quote | Order, ...current] : current.map((item) => item.id === document.id ? document as Quote | Order : item)); setEditing(null); setFeedback('Documento salvo com sucesso.') }
  const changeStatus = async (document: Quote | Order, next: string) => { try { const updated = isQuote ? await api.updateQuoteStatus(document.id, next as QuoteStatus) : await api.updateOrderStatus(document.id, next as OrderStatus); setDocuments((current) => current.map((item) => item.id === updated.id ? updated : item)); setSelected(updated); setFeedback('Status atualizado com sucesso.') } catch (actionError) { setFeedback(getApiErrorMessage(actionError, 'Não foi possível alterar o status.')) } }
  const convert = async (document: Quote | Order) => { try { if (isQuote) { const order = await api.convertQuoteToOrder(document.id); setFeedback(`Pedido ${order.numero} criado com sucesso.`) } else { await api.convertOrderToSale(document.id); setFeedback('Venda criada com sucesso.') } load() } catch (actionError) { setFeedback(getApiErrorMessage(actionError, 'Não foi possível concluir a conversão.')) } }
  return <div className="crud-page">
    <div className="crud-page-header"><PageHeader eyebrow="Comercial" title={documentTitle(kind)} description="Opere o fluxo comercial com documentos rastreáveis." pageId="settings" /><button className="button button-primary" type="button" onClick={() => setEditing('create')}>+ Novo documento</button></div>
    {feedback ? <FeedbackBanner kind="success" message={feedback} onDismiss={() => setFeedback(null)} /> : null}
    <section className="filter-toolbar"><label className="form-field"><span>Pesquisar</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Número ou cliente" /></label><label className="form-field"><span>Status</span><select value={status} onChange={(event) => setStatus(event.target.value)}><option value="">Todos</option>{(isQuote ? ['RASCUNHO', 'ENVIADO', 'APROVADO', 'RECUSADO', 'EXPIRADO', 'CANCELADO'] : ['RASCUNHO', 'CONFIRMADO', 'CONCLUIDO', 'CANCELADO']).map((value) => <option value={value} key={value}>{statusLabel(value)}</option>)}</select></label></section>
    {loading ? <LoadingState label={`Carregando ${documentTitle(kind).toLowerCase()}...`} /> : error ? <ErrorState description={error} onRetry={load} /> : documents.length === 0 ? <div className="data-card"><EmptyState title={`Nenhum ${isQuote ? 'orçamento' : 'pedido'} encontrado`} description="Crie o primeiro documento para iniciar o fluxo comercial." /></div> : <div className="data-card data-table-wrap" {...tableCustomization}><table className="data-table"><thead><tr><th>Número</th><th>Cliente</th><th>Status</th><th>Total</th><th><span className="sr-only">Ações</span></th></tr></thead><tbody>{documents.map((document) => <tr key={document.id}><td className="data-primary">{document.numero}<span className="data-secondary">#{document.id}</span></td><td>{customerName(document.cliente_id)}</td><td>{statusLabel(document.status)}</td><td>{money(document.total)}</td><td><div className="table-actions"><button className="table-action" type="button" onClick={() => setSelected(document)}>Ver</button>{canEdit(document) ? <button className="table-action" type="button" onClick={() => setEditing(document)}>Editar</button> : null}<a className="table-action" href={`${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'}${isQuote ? api.quotePrintUrl(document.id) : api.orderPrintUrl(document.id)}`} target="_blank" rel="noreferrer">Imprimir</a></div></td></tr>)}</tbody></table></div>}
    {editing ? <Modal title={editing === 'create' ? `Novo ${isQuote ? 'orçamento' : 'pedido'}` : `Editar ${isQuote ? 'orçamento' : 'pedido'}`} size="large" onClose={() => setEditing(null)}><DocumentForm kind={kind} document={editing === 'create' ? undefined : editing} onSaved={saved} onCancel={() => setEditing(null)} /></Modal> : null}
    {selected ? <Modal title={`${isQuote ? 'Orçamento' : 'Pedido'} ${selected.numero}`} size="large" onClose={() => setSelected(null)}><DocumentDetails document={selected} kind={kind} customerName={customerName} onStatus={(next) => void changeStatus(selected, next)} onConvert={() => void convert(selected)} /></Modal> : null}
  </div>
}

export function QuotesPage() { return <CommercialListPage kind="quote" /> }
export function OrdersPage() { return <CommercialListPage kind="order" /> }

export function PaymentConditionsPage() {
  const [conditions, setConditions] = useState<PaymentCondition[]>([])
  const [editing, setEditing] = useState<PaymentCondition | 'create' | null>(null)
  const [form, setForm] = useState({ codigo: '', nome: '', descricao: '' })
  const [error, setError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)
  const load = () => { api.listPaymentConditions(true).then(setConditions).catch((loadError) => setError(getApiErrorMessage(loadError, 'Não foi possível carregar as condições.'))) }
  useEffect(load, [])
  const open = (condition?: PaymentCondition) => { setForm(condition ? { codigo: condition.codigo, nome: condition.nome, descricao: condition.descricao ?? '' } : { codigo: '', nome: '', descricao: '' }); setEditing(condition ?? 'create') }
  const save = async (event: FormEvent) => {
    event.preventDefault()
    const currentEditing = editing
    if (!currentEditing) return
    try {
      const result = currentEditing === 'create'
        ? await api.createPaymentCondition({ ...form, descricao: form.descricao || null })
        : await api.updatePaymentCondition(currentEditing.id, { ...form, descricao: form.descricao || null })
      setConditions((current) => currentEditing === 'create' ? [...current, result] : current.map((item) => item.id === result.id ? result : item))
      setEditing(null)
      setFeedback('Condição salva com sucesso.')
    } catch (saveError) { setError(getApiErrorMessage(saveError, 'Não foi possível salvar a condição.')) }
  }
  const toggle = async (condition: PaymentCondition) => { try { const result = await api.updatePaymentCondition(condition.id, { ativo: !condition.ativo }); setConditions((current) => current.map((item) => item.id === result.id ? result : item)); setFeedback('Status da condição atualizado.') } catch (toggleError) { setError(getApiErrorMessage(toggleError, 'Não foi possível alterar o status.')) } }
  return <div className="crud-page"><div className="crud-page-header"><PageHeader eyebrow="Configurações" title="Condições de pagamento" description="Defina as condições usadas nos documentos comerciais." pageId="settings" /><button className="button button-primary" type="button" onClick={() => open()}>+ Nova condição</button></div>{feedback ? <FeedbackBanner kind="success" message={feedback} onDismiss={() => setFeedback(null)} /> : null}{error ? <FeedbackBanner kind="error" message={error} onDismiss={() => setError(null)} /> : null}<div className="data-card data-table-wrap"><table className="data-table"><thead><tr><th>Código</th><th>Nome</th><th>Descrição</th><th>Status</th><th>Ações</th></tr></thead><tbody>{conditions.map((condition) => <tr key={condition.id}><td>{condition.codigo}</td><td className="data-primary">{condition.nome}</td><td>{condition.descricao || '—'}</td><td>{condition.ativo ? 'Ativa' : 'Inativa'}</td><td><button className="table-action" type="button" onClick={() => open(condition)}>Editar</button><button className="table-action" type="button" onClick={() => void toggle(condition)}>{condition.ativo ? 'Inativar' : 'Ativar'}</button></td></tr>)}</tbody></table></div>{editing ? <Modal title={editing === 'create' ? 'Nova condição' : 'Editar condição'} onClose={() => setEditing(null)}><form onSubmit={save}><label className="form-field"><span>Código</span><input required value={form.codigo} onChange={(event) => setForm({ ...form, codigo: event.target.value })} /></label><label className="form-field"><span>Nome</span><input required value={form.nome} onChange={(event) => setForm({ ...form, nome: event.target.value })} /></label><label className="form-field"><span>Descrição</span><textarea value={form.descricao} onChange={(event) => setForm({ ...form, descricao: event.target.value })} /></label><div className="form-actions"><button className="button button-secondary" type="button" onClick={() => setEditing(null)}>Cancelar</button><button className="button button-primary" type="submit">Salvar condição</button></div></form></Modal> : null}</div>
}

function ReturnForm({ sale, onSaved, onCancel }: { sale: Sale; onSaved: (record: SaleReturn) => void; onCancel: () => void }) {
  const [reason, setReason] = useState('')
  const [quantities, setQuantities] = useState<Record<number, string>>({})
  const [error, setError] = useState<string | null>(null)
  const submit = async (event: FormEvent) => { event.preventDefault(); const itens = sale.itens.map((item) => ({ venda_item_id: item.id, quantidade: quantities[item.id] || '0' })).filter((item) => Number(item.quantidade) > 0); if (!reason.trim() || itens.length === 0) { setError('Informe o motivo e pelo menos um item devolvido.'); return } try { onSaved(await api.createReturn(sale.id, { motivo: reason.trim(), itens })) } catch (saveError) { setError(getApiErrorMessage(saveError, 'Não foi possível registrar a devolução.')) } }
  return <form onSubmit={submit}>{error ? <FeedbackBanner kind="error" message={error} /> : null}<label className="form-field"><span>Motivo</span><textarea required value={reason} onChange={(event) => setReason(event.target.value)} /></label>{sale.itens.map((item) => <label className="form-field" key={item.id}><span>{item.produto.nome} · máximo {item.quantidade}</span><input min="0" max={Number(item.quantidade)} step="0.001" type="number" value={quantities[item.id] ?? ''} onChange={(event) => setQuantities({ ...quantities, [item.id]: event.target.value })} /></label>)}<div className="form-actions"><button className="button button-secondary" type="button" onClick={onCancel}>Cancelar</button><button className="button button-primary" type="submit">Registrar devolução</button></div></form>
}

export function ReturnsPage() {
  const [returns, setReturns] = useState<SaleReturn[]>([])
  const [sales, setSales] = useState<Sale[]>([])
  const [selectedSale, setSelectedSale] = useState<Sale | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)
  useEffect(() => { Promise.all([api.listReturns(), listSales({ page: 1, pageSize: 100 })]).then(([returnList, saleList]) => { setReturns(returnList); setSales(saleList) }).catch((loadError) => setError(getApiErrorMessage(loadError, 'Não foi possível carregar as devoluções.'))) }, [])
  const saleOptions = useMemo(() => sales.filter((sale) => sale.status !== 'CANCELADA'), [sales])
  const save = (record: SaleReturn) => { setReturns((current) => [record, ...current]); setSelectedSale(null); setFeedback('Devolução registrada em rascunho.') }
  const approve = async (record: SaleReturn) => { try { const approved = await api.approveReturn(record.id); setReturns((current) => current.map((item) => item.id === approved.id ? approved : item)); setFeedback('Devolução aprovada e estoque atualizado.') } catch (approveError) { setError(getApiErrorMessage(approveError, 'Não foi possível aprovar a devolução.')) } }
  return <div className="crud-page"><div className="crud-page-header"><PageHeader eyebrow="Comercial" title="Devoluções" description="Registre devoluções totais ou parciais e acompanhe seu efeito." pageId="returns" /><button className="button button-primary" type="button" onClick={() => { if (saleOptions[0]) setSelectedSale(saleOptions[0]); else setError('Não há vendas disponíveis para devolução.') }}>+ Nova devolução</button></div>{feedback ? <FeedbackBanner kind="success" message={feedback} onDismiss={() => setFeedback(null)} /> : null}{error ? <FeedbackBanner kind="error" message={error} onDismiss={() => setError(null)} /> : null}<div className="data-card data-table-wrap"><table className="data-table"><thead><tr><th>Devolução</th><th>Venda</th><th>Motivo</th><th>Status</th><th>Ações</th></tr></thead><tbody>{returns.map((record) => <tr key={record.id}><td>#{record.id}</td><td>#{record.venda_id}</td><td>{record.motivo}</td><td>{record.status}</td><td>{record.status === 'RASCUNHO' ? <button className="table-action" type="button" onClick={() => void approve(record)}>Aprovar</button> : null}</td></tr>)}</tbody></table>{returns.length === 0 ? <EmptyState title="Nenhuma devolução registrada" description="As devoluções aparecerão aqui após o primeiro registro." /> : null}</div>{selectedSale ? <Modal title={`Devolução da venda #${selectedSale.id}`} onClose={() => setSelectedSale(null)}><ReturnForm sale={selectedSale} onSaved={save} onCancel={() => setSelectedSale(null)} /></Modal> : null}</div>
}
