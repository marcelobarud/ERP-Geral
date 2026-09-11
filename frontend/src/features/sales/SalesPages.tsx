import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from 'react'

import { EmptyState } from '../../components/EmptyState'
import { ErrorState } from '../../components/ErrorState'
import { FeedbackBanner } from '../../components/FeedbackBanner'
import { FilterMenu } from '../../components/FilterMenu'
import { LoadingState } from '../../components/LoadingState'
import { Modal } from '../../components/Modal'
import { PaginationControls } from '../../components/PaginationControls'
import { PageHeader } from '../../components/PageHeader'
import { SearchInput } from '../../components/SearchInput'
import { ApiError, getApiErrorMessage } from '../../services/httpClient'
import { getPaginationMeta, type PaginationMeta } from '../../types/pagination'
import { listCustomers } from '../customers/api'
import type { Customer } from '../customers/types'
import { listEmployees } from '../employees/api'
import type { Employee } from '../employees/types'
import { listProducts } from '../products/api'
import type { Product } from '../products/types'
import { useCustomizable } from '../settings/VisualCustomizationContext'
import { cancelSale, createSale, getSale, listSales, type SaleListFilters } from './api'
import type { Sale, SaleCreatePayload, SaleStatus } from './types'

type DraftSaleItem = {
  key: number
  produtoId: number | ''
  quantidade: string
}

const moneyScale = 100n
const quantityScale = 1000n

function normalizeDecimal(value: string | number): string {
  return String(value).trim().replace(',', '.')
}

function decimalToScaled(value: string | number, scale: bigint): bigint | null {
  const normalized = normalizeDecimal(value)
  if (!/^\d+(?:\.\d+)?$/.test(normalized)) return null

  const [integerPart, fractionPart = ''] = normalized.split('.')
  const scaleLength = scale === moneyScale ? 2 : 3
  const fraction = (fractionPart + '0'.repeat(scaleLength)).slice(0, scaleLength)
  return BigInt(integerPart) * scale + BigInt(fraction)
}

function scaledToDecimal(value: bigint, scale: bigint): string {
  const integerPart = value / scale
  const fractionPart = String(value % scale).padStart(String(scale).length - 1, '0')
  return `${integerPart}.${fractionPart}`
}

function multiplyQuantityByPrice(quantity: string, price: string | number): string {
  const quantityScaled = decimalToScaled(quantity, quantityScale)
  const priceScaled = decimalToScaled(price, moneyScale)
  if (quantityScaled === null || priceScaled === null) return '0.00'

  const raw = quantityScaled * priceScaled
  const divisor = quantityScale
  let cents = raw / divisor
  if (raw % divisor >= divisor / 2n) cents += 1n
  return scaledToDecimal(cents, moneyScale)
}

function addMoney(left: string, right: string): string {
  const leftScaled = decimalToScaled(left, moneyScale) ?? 0n
  const rightScaled = decimalToScaled(right, moneyScale) ?? 0n
  return scaledToDecimal(leftScaled + rightScaled, moneyScale)
}

function formatMoney(value: string | number): string {
  const normalized = normalizeDecimal(value)
  const [integerPart = '0', fractionPart = ''] = normalized.split('.')
  const integer = integerPart.replace(/^0+(?=\d)/, '') || '0'
  const grouped = integer.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
  return `R$ ${grouped},${(fractionPart + '00').slice(0, 2)}`
}

function formatDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(date)
}

function defaultSaleDate(): string {
  const now = new Date()
  const offset = now.getTimezoneOffset() * 60000
  return new Date(now.getTime() - offset).toISOString().slice(0, 16)
}

function normalizeQuantity(value: string): string | null {
  const normalized = normalizeDecimal(value)
  if (!/^\d+(?:\.\d{1,3})?$/.test(normalized)) return null
  const scaled = decimalToScaled(normalized, quantityScale)
  return scaled && scaled > 0n ? normalized : null
}

function saleErrorMessage(error: unknown, fallback: string): string {
  return getApiErrorMessage(error, fallback)
}

function saleProductLabel(sale: Sale): string {
  const productNames = new Map(sale.itens.map((item) => [item.produto.id, item.produto.nome]))
  if (productNames.size === 1) return productNames.values().next().value ?? 'Produto'
  return `${productNames.size} produtos`
}

function SaleItemRow({
  item,
  products,
  selectedProductIds,
  onChange,
  onRemove,
}: {
  item: DraftSaleItem
  products: Product[]
  selectedProductIds: number[]
  onChange: (patch: Partial<DraftSaleItem>) => void
  onRemove: () => void
}) {
  const selectedProduct = products.find((product) => product.id === item.produtoId)
  const availableProducts = products.filter(
    (product) =>
      product.id === item.produtoId || !selectedProductIds.includes(product.id),
  )
  const subtotal = selectedProduct
    ? multiplyQuantityByPrice(item.quantidade, selectedProduct.preco_venda)
    : '0.00'

  return (
    <div className="sale-item-row">
      <div className="form-field sale-item-product">
        <label htmlFor={`sale-product-${item.key}`}>Produto do item {item.key}</label>
        <select
          id={`sale-product-${item.key}`}
          required
          value={item.produtoId}
          onChange={(event) => onChange({ produtoId: Number(event.target.value) })}
        >
          <option value="" disabled>
            Selecione um produto
          </option>
          {availableProducts.map((product) => (
            <option value={product.id} key={product.id}>
              {product.nome} · {product.categoria} · {formatMoney(product.preco_venda)}
            </option>
          ))}
        </select>
      </div>
      <div className="form-field sale-item-quantity">
        <label htmlFor={`sale-quantity-${item.key}`}>Quantidade</label>
        <input
          id={`sale-quantity-${item.key}`}
          required
          inputMode="decimal"
          placeholder="1.000"
          type="text"
          value={item.quantidade}
          onChange={(event) => onChange({ quantidade: event.target.value })}
        />
        <span className="form-help">Aceita até três casas decimais.</span>
      </div>
      <div className="sale-item-value">
        <span className="sale-item-label">Preço unitário</span>
        <strong>{selectedProduct ? formatMoney(selectedProduct.preco_venda) : '—'}</strong>
        <span className="sale-item-note">Definido pelo catálogo</span>
      </div>
      <div className="sale-item-value">
        <span className="sale-item-label">Subtotal visual</span>
        <strong>{selectedProduct ? formatMoney(subtotal) : '—'}</strong>
        <span className="sale-item-note">Confirmado pelo backend</span>
      </div>
      <button className="table-action table-action-danger sale-remove" type="button" onClick={onRemove}>
        Remover
      </button>
    </div>
  )
}

export function NewSalePage() {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [employees, setEmployees] = useState<Employee[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [customerId, setCustomerId] = useState<number | ''>('')
  const [employeeId, setEmployeeId] = useState<number | ''>('')
  const [saleDate, setSaleDate] = useState(defaultSaleDate)
  const [saleObservation, setSaleObservation] = useState('')
  const [items, setItems] = useState<DraftSaleItem[]>([])
  const [nextItemKey, setNextItemKey] = useState(1)
  const [saving, setSaving] = useState(false)
  const [createdSale, setCreatedSale] = useState<Sale | null>(null)
  const contextCustomization = useCustomizable({ key: 'new_sale.context_card', type: 'SURFACE', group: 'sale-card', page: 'new_sale', label: 'Dados da venda' })
  const itemsCustomization = useCustomizable({ key: 'new_sale.items_card', type: 'SURFACE', group: 'sale-card', page: 'new_sale', label: 'Itens da venda' })
  const submitCustomization = useCustomizable({ key: 'new_sale.submit_button', type: 'BUTTON', group: 'primary-action', page: 'new_sale', label: 'Salvar venda' })

  const loadSaleDependencies = useCallback(async () => {
    setLoading(true)
    setLoadError(null)
    try {
      const [customerList, employeeList, productList] = await Promise.all([
        listCustomers({ page: 1, pageSize: 100 }),
        listEmployees(true, '', { page: 1, pageSize: 100 }),
        listProducts({ page: 1, pageSize: 100 }),
      ])
      setCustomers(customerList)
      setEmployees(employeeList)
      setProducts(productList)
    } catch (error) {
      setLoadError(saleErrorMessage(error, 'Não foi possível carregar os dados da venda.'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect
    void loadSaleDependencies()
  }, [loadSaleDependencies])

  const selectedProductIds = items
    .map((item) => item.produtoId)
    .filter((id): id is number => typeof id === 'number')
  const visualTotal = useMemo(
    () =>
      items.reduce((total, item) => {
        const product = products.find((candidate) => candidate.id === item.produtoId)
        return product
          ? addMoney(total, multiplyQuantityByPrice(item.quantidade, product.preco_venda))
          : total
      }, '0.00'),
    [items, products],
  )
  const prerequisitesReady = customers.length > 0 && employees.length > 0 && products.length > 0

  const addItem = () => {
    setItems((current) => [...current, { key: nextItemKey, produtoId: '', quantidade: '1' }])
    setNextItemKey((current) => current + 1)
    setSubmitError(null)
  }

  const updateItem = (key: number, patch: Partial<DraftSaleItem>) => {
    setItems((current) => current.map((item) => (item.key === key ? { ...item, ...patch } : item)))
    setSubmitError(null)
  }

  const removeItem = (key: number) => {
    setItems((current) => current.filter((item) => item.key !== key))
    setSubmitError(null)
  }

  const resetForm = () => {
    setCustomerId('')
    setEmployeeId('')
    setSaleDate(defaultSaleDate())
    setSaleObservation('')
    setItems([])
    setCreatedSale(null)
    setFeedback(null)
    setSubmitError(null)
  }

  const submitSale = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSubmitError(null)

    if (customerId === '' || employeeId === '') {
      setSubmitError('Selecione um cliente e um funcionário para continuar.')
      return
    }
    if (items.length === 0) {
      setSubmitError('Adicione pelo menos um produto à venda.')
      return
    }

    const normalizedItems: SaleCreatePayload['itens'] = []
    const seenProductIds = new Set<number>()
    for (const item of items) {
      if (item.produtoId === '') {
        setSubmitError('Selecione um produto para cada item.')
        return
      }
      const quantity = normalizeQuantity(item.quantidade)
      if (quantity === null) {
        setSubmitError('Informe quantidades maiores que zero com até três casas decimais.')
        return
      }
      if (seenProductIds.has(item.produtoId)) {
        setSubmitError('Cada produto só pode aparecer uma vez na mesma venda.')
        return
      }
      seenProductIds.add(item.produtoId)
      normalizedItems.push({ produto_id: item.produtoId, quantidade: quantity })
    }

    const parsedDate = new Date(saleDate)
    if (Number.isNaN(parsedDate.getTime())) {
      setSubmitError('Informe uma data válida para a venda.')
      return
    }

    setSaving(true)
    try {
      const payload: SaleCreatePayload = {
        cliente_id: customerId,
        funcionario_id: employeeId,
        data_venda: parsedDate.toISOString(),
        itens: normalizedItems,
      }
      if (saleObservation.trim()) payload.observacao = saleObservation.trim()
      const saved = await createSale(payload)
      setCreatedSale(saved)
      setFeedback(`Venda #${saved.id} criada com sucesso. Total confirmado: ${formatMoney(saved.total)}.`)
      setCustomerId('')
      setEmployeeId('')
      setSaleDate(defaultSaleDate())
      setSaleObservation('')
      setItems([])
    } catch (error) {
      setSubmitError(saleErrorMessage(error, 'Não foi possível criar a venda.'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="sales-page">
      <div className="sales-page-header">
        <PageHeader eyebrow="Vendas" title="Nova venda" description="Monte uma venda com segurança e acompanhe os valores antes de confirmar." pageId="new_sale" />
        <a className="button button-secondary" href="/sales">Ver vendas</a>
      </div>
      {feedback ? <FeedbackBanner kind="success" message={feedback} onDismiss={() => setFeedback(null)} /> : null}
      {submitError ? <FeedbackBanner kind="error" message={submitError} onDismiss={() => setSubmitError(null)} /> : null}
      {loadError ? <ErrorState description={loadError} onRetry={() => void loadSaleDependencies()} /> : null}
      {createdSale ? (
        <div className="sale-created-card">
          <div>
            <strong>Venda #{createdSale.id} disponível</strong>
            <p>Consulte os preços históricos e os itens gravados pelo backend.</p>
          </div>
          <a className="button button-primary" href="/sales">Abrir lista de vendas</a>
        </div>
      ) : null}
      {loading ? <LoadingState label="Carregando clientes, funcionários e produtos..." /> : (
        <form className="sale-layout" onSubmit={submitSale}>
          <section className="sale-card" {...contextCustomization}>
            <div className="sale-section-heading">
              <div><p className="eyebrow">Contexto</p><h2>Dados da venda</h2></div>
              <span className="sale-step">1</span>
            </div>
            <div className="form-grid">
              <div className="form-field">
                <label htmlFor="sale-customer">Cliente</label>
                <select id="sale-customer" required value={customerId} onChange={(event) => setCustomerId(Number(event.target.value) || '')}>
                  <option value="" disabled>Selecione um cliente</option>
                  {customers.map((customer) => <option value={customer.id} key={customer.id}>{customer.nome}</option>)}
                </select>
                {customers.length === 0 ? <span className="form-help form-help-warning">Cadastre um cliente antes de vender.</span> : null}
              </div>
              <div className="form-field">
                <label htmlFor="sale-employee">Funcionário</label>
                <select id="sale-employee" required value={employeeId} onChange={(event) => setEmployeeId(Number(event.target.value) || '')}>
                  <option value="" disabled>Selecione um funcionário</option>
                  {employees.map((employee) => <option value={employee.id} key={employee.id}>{employee.nome_completo}</option>)}
                </select>
                {employees.length === 0 ? <span className="form-help form-help-warning">Cadastre um funcionário antes de vender.</span> : null}
              </div>
              <div className="form-field form-grid-wide">
                <label htmlFor="sale-date">Data da venda</label>
                <input id="sale-date" required type="datetime-local" value={saleDate} onChange={(event) => setSaleDate(event.target.value)} />
              </div>
              <div className="form-field form-grid-wide">
                <label htmlFor="sale-observation">Observação (opcional)</label>
                <textarea id="sale-observation" maxLength={1000} value={saleObservation} onChange={(event) => setSaleObservation(event.target.value)} />
              </div>
            </div>
          </section>

          <section className="sale-card sale-items-card" {...itemsCustomization}>
            <div className="sale-section-heading">
              <div><p className="eyebrow">Composição</p><h2>Itens da venda</h2><p className="sale-section-description">O preço unitário é somente informativo e será confirmado pelo backend.</p></div>
              <span className="sale-step">2</span>
            </div>
            {products.length === 0 ? <div className="sale-prerequisite"><strong>Nenhum produto disponível</strong><span>Cadastre um produto antes de criar uma venda.</span></div> : null}
            {items.length === 0 ? <div className="sale-items-empty"><strong>Adicione o primeiro produto</strong><span>Você poderá incluir vários produtos, alterar quantidades e remover itens antes de salvar.</span></div> : (
              <div className="sale-item-list">
                {items.map((item) => <SaleItemRow key={item.key} item={item} products={products} selectedProductIds={selectedProductIds.filter((id) => id !== item.produtoId)} onChange={(patch) => updateItem(item.key, patch)} onRemove={() => removeItem(item.key)} />)}
              </div>
            )}
            <div className="sale-items-actions">
              <button className="button button-secondary" type="button" onClick={addItem} disabled={products.length === 0 || selectedProductIds.length >= products.length}>+ Adicionar produto</button>
              {selectedProductIds.length >= products.length && products.length > 0 ? <span className="form-help">Todos os produtos disponíveis já foram adicionados.</span> : null}
            </div>
          </section>

          <aside className="sale-summary-card">
            <p className="eyebrow">Resumo</p>
            <h2>Total da venda</h2>
            <strong className="sale-total">{formatMoney(visualTotal)}</strong>
            <p>Estimativa visual com o preço atual do catálogo. O total definitivo será retornado pelo backend.</p>
            <button className="button button-primary sale-submit" type="submit" {...submitCustomization} disabled={saving || !prerequisitesReady || items.length === 0}>
              {saving ? 'Salvando venda...' : 'Salvar venda'}
            </button>
          </aside>
        </form>
      )}
      {createdSale ? <button className="text-button sale-new-button" type="button" onClick={resetForm}>Criar outra venda</button> : null}
    </div>
  )
}

function formatQuantityForDisplay(value: string | number): string {
  return normalizeDecimal(value).replace('.', ',')
}

function SaleDetails({ sale, onCancel }: { sale: Sale; onCancel: () => void }) {
  const saleStatus = sale.status ?? 'CONCLUIDA'
  return (
    <div className="sale-details">
      <dl className="detail-grid sale-detail-meta">
        <div><dt>ID</dt><dd>#{sale.id}</dd></div><div><dt>Data</dt><dd>{formatDate(sale.data_venda)}</dd></div><div><dt>Status</dt><dd><span className={`status-badge ${saleStatus === 'CANCELADA' ? 'status-badge-inactive' : 'status-badge-active'}`}>{saleStatus === 'CANCELADA' ? 'Cancelada' : 'Concluída'}</span></dd></div><div><dt>Cliente</dt><dd>{sale.cliente.nome}</dd></div><div><dt>Funcionário</dt><dd>{sale.funcionario.nome_completo}</dd></div>
      </dl>
      {sale.observacao ? <p className="sale-observation"><strong>Observação:</strong> {sale.observacao}</p> : null}
      {sale.motivo_cancelamento ? <p className="sale-observation"><strong>Motivo do cancelamento:</strong> {sale.motivo_cancelamento}</p> : null}
      <div className="sale-detail-items">
        <div className="sale-detail-heading"><h3>Itens</h3><span>Valores históricos</span></div>
        {sale.itens.map((item) => (
          <div className="sale-detail-item" key={item.id}>
            <div>
              <span className="sale-detail-field-label">Produto</span>
              <strong>{item.produto.nome}</strong>
            </div>
            <div>
              <span className="sale-detail-field-label">Quantidade</span>
              <strong>{formatQuantityForDisplay(item.quantidade)}</strong>
            </div>
            <div>
              <span className="sale-detail-field-label">Preço unitário</span>
              <strong>{formatMoney(item.preco_unitario)}</strong>
            </div>
            <div>
              <span className="sale-detail-field-label">Subtotal</span>
              <strong>{formatMoney(item.subtotal)}</strong>
            </div>
            <div>
              <span className="sale-detail-field-label">Fornecedor histórico</span>
              <strong>{item.fornecedor.nome}</strong>
            </div>
          </div>
        ))}
      </div>
      <div className="sale-detail-total"><span>Total da venda</span><strong>{formatMoney(sale.total)}</strong></div>
      {saleStatus === 'CONCLUIDA' ? <div className="sale-detail-actions"><button className="button button-danger" type="button" onClick={onCancel}>Cancelar venda</button></div> : null}
    </div>
  )
}

export function SalesPage() {
  const [sales, setSales] = useState<Sale[]>([])
  const [page, setPage] = useState(1)
  const [pagination, setPagination] = useState<PaginationMeta>({ page: 1, page_size: 20, total: 0, total_pages: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedSaleId, setSelectedSaleId] = useState<number | null>(null)
  const [selectedSale, setSelectedSale] = useState<Sale | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState<string | null>(null)
  const [cancelTarget, setCancelTarget] = useState<Sale | null>(null)
  const [cancelError, setCancelError] = useState<string | null>(null)
  const [cancellingSaleId, setCancellingSaleId] = useState<number | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [searchDraft, setSearchDraft] = useState('')
  const [productIdDraft, setProductIdDraft] = useState<number | ''>('')
  const [customerIdDraft, setCustomerIdDraft] = useState<number | ''>('')
  const [employeeIdDraft, setEmployeeIdDraft] = useState<number | ''>('')
  const [dateFromDraft, setDateFromDraft] = useState('')
  const [dateToDraft, setDateToDraft] = useState('')
  const [totalMinDraft, setTotalMinDraft] = useState('')
  const [totalMaxDraft, setTotalMaxDraft] = useState('')
  const [statusDraft, setStatusDraft] = useState<SaleStatus | ''>('')
  const [appliedFilters, setAppliedFilters] = useState<SaleListFilters>({})
  const [filterCustomers, setFilterCustomers] = useState<Customer[]>([])
  const [filterEmployees, setFilterEmployees] = useState<Employee[]>([])
  const [filterProducts, setFilterProducts] = useState<Product[]>([])
  const [optionsLoading, setOptionsLoading] = useState(true)
  const [filtersOpen, setFiltersOpen] = useState(false)
  const loadRequestId = useRef(0)
  const tableCustomization = useCustomizable({ key: 'sales.table', type: 'TABLE', group: 'data-table', page: 'sales', label: 'Histórico de vendas' })

  const loadSales = useCallback(async () => {
    const requestId = ++loadRequestId.current
    setLoading(true)
    setError(null)
    try {
      const saleList = await listSales({ ...appliedFilters, page, pageSize: 20 })
      if (requestId !== loadRequestId.current) return
      setSales(saleList)
      setPagination(getPaginationMeta(saleList))
    } catch (loadError) {
      if (requestId === loadRequestId.current) setError(saleErrorMessage(loadError, 'Não foi possível carregar as vendas.'))
    } finally {
      if (requestId === loadRequestId.current) setLoading(false)
    }
  }, [appliedFilters, page])

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect
    void loadSales()
  }, [loadSales])

  useEffect(() => {
    let mounted = true
    Promise.all([
      listCustomers({ page: 1, pageSize: 100 }),
      listEmployees(false, '', { page: 1, pageSize: 100 }),
      listProducts({ page: 1, pageSize: 100 }),
    ])
      .then(([customerList, employeeList, productList]) => {
        if (!mounted) return
        setFilterCustomers(customerList)
        setFilterEmployees(employeeList)
        setFilterProducts(productList)
      })
      .catch((loadError) => {
        if (mounted) setError(saleErrorMessage(loadError, 'Não foi possível carregar as opções de filtros.'))
      })
      .finally(() => { if (mounted) setOptionsLoading(false) })
    return () => { mounted = false }
  }, [])

  const hasDraftFilters = Boolean(searchDraft.trim() || productIdDraft !== '' || customerIdDraft !== '' || employeeIdDraft !== '' || dateFromDraft || dateToDraft || totalMinDraft.trim() || totalMaxDraft.trim() || statusDraft)
  const hasAppliedFilters = Boolean(appliedFilters.search || appliedFilters.productId || appliedFilters.customerId || appliedFilters.employeeId || appliedFilters.dateFrom || appliedFilters.dateTo || appliedFilters.totalMin || appliedFilters.totalMax || appliedFilters.status)
  const applyFilters = () => { setPage(1); setAppliedFilters({ search: searchDraft.trim(), productId: productIdDraft, customerId: customerIdDraft, employeeId: employeeIdDraft, dateFrom: dateFromDraft, dateTo: dateToDraft, totalMin: totalMinDraft.trim(), totalMax: totalMaxDraft.trim(), status: statusDraft || undefined }); setFiltersOpen(false) }
  const clearFilters = () => { setPage(1); setSearchDraft(''); setProductIdDraft(''); setCustomerIdDraft(''); setEmployeeIdDraft(''); setDateFromDraft(''); setDateToDraft(''); setTotalMinDraft(''); setTotalMaxDraft(''); setStatusDraft(''); setAppliedFilters({}); setFiltersOpen(false) }

  const openSaleDetails = async (saleId: number) => {
    setSelectedSaleId(saleId)
    setSelectedSale(null)
    setDetailError(null)
    setDetailLoading(true)
    try {
      setSelectedSale(await getSale(saleId))
    } catch (detailLoadError) {
      setDetailError(saleErrorMessage(detailLoadError, 'Não foi possível carregar os detalhes da venda.'))
    } finally {
      setDetailLoading(false)
    }
  }

  const closeDetails = () => {
    setSelectedSaleId(null)
    setSelectedSale(null)
    setDetailError(null)
  }

  const requestSaleCancellation = (sale: Sale) => {
    setCancelTarget(sale)
    setCancelError(null)
  }

  const confirmSaleCancellation = async () => {
    if (cancelTarget === null) return

    const saleId = cancelTarget.id
    setCancellingSaleId(saleId)
    setCancelError(null)
    try {
      const cancelled = await cancelSale(saleId, cancelTarget.motivo_cancelamento ?? undefined)
      setSales((current) => current.map((sale) => sale.id === saleId ? cancelled : sale))
      setCancelTarget(null)
      setFeedback(`Venda #${saleId} cancelada com sucesso.`)
      if (selectedSaleId === saleId) setSelectedSale(cancelled)
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        setCancelTarget(null)
        setFeedback(`A venda #${saleId} já não estava disponível. A lista foi atualizada.`)
      } else {
        setCancelError(getApiErrorMessage(error, 'Não foi possível cancelar a venda. Tente novamente.'))
      }
    } finally {
      setCancellingSaleId(null)
    }
  }

  return (
    <div className="sales-page">
      <div className="sales-page-header">
        <PageHeader eyebrow="Vendas" title="Vendas" description="Consulte o histórico das vendas e seus preços históricos." pageId="sales" />
        <a className="button button-primary" href="/sales/new">+ Nova venda</a>
      </div>
      {feedback ? <FeedbackBanner kind="success" message={feedback} onDismiss={() => setFeedback(null)} /> : null}
      <section className="filter-toolbar" aria-label="Filtros de vendas">
        <SearchInput value={searchDraft} onChange={setSearchDraft} onSearch={(value) => setAppliedFilters((current) => { const search = value.trim(); if (current.search === search) return current; const { search: _search, ...filters } = current; return search ? { ...filters, search } : filters })} onClear={() => setSearchDraft('')} label="Pesquisar vendas" customizationKey="sales.search_input" customizationPage="sales" />
        <FilterMenu activeCount={[appliedFilters.productId, appliedFilters.customerId, appliedFilters.employeeId, appliedFilters.dateFrom, appliedFilters.dateTo, appliedFilters.totalMin, appliedFilters.totalMax, appliedFilters.status].filter(Boolean).length} canClear={hasDraftFilters || hasAppliedFilters} open={filtersOpen} onToggle={() => setFiltersOpen((current) => !current)} onClose={() => setFiltersOpen(false)} onApply={applyFilters} onClear={clearFilters}>
          <label className="filter-field">Produto<select value={productIdDraft} onChange={(event) => setProductIdDraft(event.target.value ? Number(event.target.value) : '')}><option value="">Todos os produtos</option>{filterProducts.map((product) => <option value={product.id} key={product.id}>{product.nome}</option>)}</select></label>
          <label className="filter-field">Cliente<select value={customerIdDraft} onChange={(event) => setCustomerIdDraft(event.target.value ? Number(event.target.value) : '')}><option value="">Todos os clientes</option>{filterCustomers.map((customer) => <option value={customer.id} key={customer.id}>{customer.nome}</option>)}</select></label>
          <label className="filter-field">Funcionário<select value={employeeIdDraft} onChange={(event) => setEmployeeIdDraft(event.target.value ? Number(event.target.value) : '')}><option value="">Todos os funcionários</option>{filterEmployees.map((employee) => <option value={employee.id} key={employee.id}>{employee.nome_completo}</option>)}</select></label>
          <label className="filter-field">Data inicial<input type="date" value={dateFromDraft} onChange={(event) => setDateFromDraft(event.target.value)} /></label>
          <label className="filter-field">Data final<input type="date" value={dateToDraft} onChange={(event) => setDateToDraft(event.target.value)} /></label>
          <label className="filter-field">Total mínimo<input type="number" min="0" step="0.01" value={totalMinDraft} onChange={(event) => setTotalMinDraft(event.target.value)} /></label>
          <label className="filter-field">Total máximo<input type="number" min="0" step="0.01" value={totalMaxDraft} onChange={(event) => setTotalMaxDraft(event.target.value)} /></label>
          <label className="filter-field">Status<select value={statusDraft} onChange={(event) => setStatusDraft(event.target.value as SaleStatus | '')}><option value="">Todos</option><option value="CONCLUIDA">Concluídas</option><option value="CANCELADA">Canceladas</option></select></label>
        </FilterMenu>
      </section>
      {loading || optionsLoading ? <LoadingState label="Carregando vendas..." /> : error ? <ErrorState description={error} onRetry={() => void loadSales()} /> : sales.length === 0 ? (
        <div className="data-card sales-empty-card"><EmptyState title={hasAppliedFilters ? 'Nenhum resultado encontrado para os filtros aplicados.' : 'Nenhuma venda registrada ainda'} description={hasAppliedFilters ? 'Tente ajustar a pesquisa ou limpar os filtros.' : 'Crie sua primeira venda para começar o histórico operacional.'} />{!hasAppliedFilters ? <a className="button button-primary" href="/sales/new">Criar nova venda</a> : null}</div>
      ) : (
        <><div className="sales-list" {...tableCustomization}>
          {sales.map((sale) => { const saleStatus = sale.status ?? 'CONCLUIDA'; return <article className="sale-list-card" key={sale.id}><div className="sale-list-header"><div><span className="sale-list-kicker">Venda</span><strong>#{sale.id}</strong></div><div><span className={`status-badge ${saleStatus === 'CANCELADA' ? 'status-badge-inactive' : 'status-badge-active'}`}>{saleStatus === 'CANCELADA' ? 'Cancelada' : 'Concluída'}</span><span className="sale-list-date">{formatDate(sale.data_venda)}</span></div></div><dl className="sale-list-meta"><div><dt>Produto</dt><dd className="sale-list-product">{saleProductLabel(sale)}</dd></div><div><dt>Valor Total</dt><dd className="sale-list-total">{formatMoney(sale.total)}</dd></div><div><dt>Cliente</dt><dd>{sale.cliente.nome}</dd></div><div><dt>Funcionário</dt><dd>{sale.funcionario.nome_completo}</dd></div></dl><div className="sale-list-actions"><button className="button button-secondary sale-detail-button" type="button" onClick={() => void openSaleDetails(sale.id)}>Ver detalhes</button>{saleStatus === 'CONCLUIDA' ? <button className="button button-danger sale-delete-button" type="button" onClick={() => requestSaleCancellation(sale)}>Cancelar venda</button> : null}</div></article> })}
        </div><PaginationControls meta={pagination} onPageChange={setPage} /></>
      )}
      {selectedSaleId !== null ? <Modal title={`Detalhes da venda #${selectedSaleId}`} description="Os preços abaixo são os valores históricos retornados pelo backend." size="large" onClose={closeDetails}>{detailLoading ? <LoadingState label="Carregando detalhes..." /> : detailError ? <ErrorState description={detailError} onRetry={() => void openSaleDetails(selectedSaleId)} /> : selectedSale ? <SaleDetails sale={selectedSale} onCancel={() => { requestSaleCancellation(selectedSale); closeDetails() }} /> : null}</Modal> : null}
      {cancelTarget ? <Modal title={`Cancelar venda #${cancelTarget.id}?`} description="A venda e seus itens serão preservados no histórico. Esta operação marcará a venda como cancelada." onClose={() => setCancelTarget(null)}>
        {cancelError ? <FeedbackBanner kind="error" message={cancelError} /> : null}
        <label className="form-field"><span>Motivo (opcional)</span><textarea maxLength={500} onChange={(event) => setCancelTarget((current) => current ? { ...current, motivo_cancelamento: event.target.value } : current)} value={cancelTarget.motivo_cancelamento ?? ''} /></label>
        <div className="confirm-actions">
          <button className="button button-secondary" type="button" onClick={() => setCancelTarget(null)} disabled={cancellingSaleId !== null}>Voltar</button>
          <button className="button button-danger" type="button" onClick={() => void confirmSaleCancellation()} disabled={cancellingSaleId !== null}>{cancellingSaleId !== null ? 'Cancelando...' : 'Cancelar venda'}</button>
        </div>
      </Modal> : null}
    </div>
  )
}
