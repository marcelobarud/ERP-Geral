import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react'

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
import { createProduct, deleteProduct, getProduct, listProductSuppliers, listProducts, updateProduct, type ProductListFilters } from './api'
import type { Product, ProductPayload } from './types'
import type { Supplier } from '../suppliers/types'

const emptyProduct: ProductPayload = { nome: '', categoria: '', preco_custo: '', preco_venda: '', fornecedor_id: 0 }
const PAGE_SIZE = 20

function displayMoney(value: string | number): string {
  return `R$ ${String(value).replace('.', ',')}`
}

function ProductForm({ initialValue, suppliers, saving, onCancel, onSave }: { initialValue: ProductPayload; suppliers: Supplier[]; saving: boolean; onCancel: () => void; onSave: (payload: ProductPayload) => void }) {
  const [form, setForm] = useState(initialValue)
  const [customValues, setCustomValues] = useState<Record<string, unknown>>({})
  const updateText = (field: 'nome' | 'categoria' | 'preco_custo' | 'preco_venda', value: string) => setForm((current) => ({ ...current, [field]: value }))
  const submit = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); onSave({ ...form, ...(Object.keys(customValues).length ? { campos_personalizados: customValues } : {}) }) }

  return <form onSubmit={submit}><div className="form-grid">
    <div className="form-field form-grid-wide"><label htmlFor="product-name">Nome</label><input id="product-name" required value={form.nome} onChange={(event) => updateText('nome', event.target.value)} /></div>
    <div className="form-field"><label htmlFor="product-category">Categoria</label><input id="product-category" required value={form.categoria} onChange={(event) => updateText('categoria', event.target.value)} /></div>
    <div className="form-field"><label htmlFor="product-supplier">Fornecedor</label><select id="product-supplier" required value={form.fornecedor_id || ''} onChange={(event) => setForm((current) => ({ ...current, fornecedor_id: Number(event.target.value) }))}><option value="" disabled>Selecione um fornecedor</option>{suppliers.map((supplier) => <option value={supplier.id} key={supplier.id}>{supplier.nome}</option>)}</select></div>
    <div className="form-field"><label htmlFor="product-cost">Preço de custo</label><input id="product-cost" required min="0" step="0.01" type="number" value={form.preco_custo} onChange={(event) => updateText('preco_custo', event.target.value)} /><span className="form-help">Use duas casas decimais.</span></div>
    <div className="form-field"><label htmlFor="product-price">Preço de venda</label><input id="product-price" required min="0" step="0.01" type="number" value={form.preco_venda} onChange={(event) => updateText('preco_venda', event.target.value)} /><span className="form-help">Use duas casas decimais.</span></div>
    <CustomFieldFields module="products" values={customValues} onChange={(name, value) => setCustomValues((current) => ({ ...current, [name]: value }))} />
  </div><div className="form-actions"><button className="button button-secondary" type="button" onClick={onCancel} disabled={saving}>Cancelar</button><button className="button button-primary" type="submit" disabled={saving}>{saving ? 'Salvando...' : 'Salvar produto'}</button></div></form>
}

function ProductDetails({ product, supplierName }: { product: Product; supplierName: string }) {
  return <><dl className="detail-grid"><div><dt>Nome</dt><dd>{product.nome}</dd></div><div><dt>Categoria</dt><dd>{product.categoria}</dd></div><div><dt>Fornecedor</dt><dd>{supplierName}</dd></div><div><dt>Preço de custo</dt><dd>{displayMoney(product.preco_custo)}</dd></div><div><dt>Preço de venda</dt><dd>{displayMoney(product.preco_venda)}</dd></div></dl><CustomFieldDetails values={product.campos_personalizados} /></>
}

export function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [filterProducts, setFilterProducts] = useState<Product[]>([])
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchDraft, setSearchDraft] = useState('')
  const [categoryDraft, setCategoryDraft] = useState('')
  const [supplierDraft, setSupplierDraft] = useState<number | ''>('')
  const [costMinDraft, setCostMinDraft] = useState('')
  const [costMaxDraft, setCostMaxDraft] = useState('')
  const [salePriceMinDraft, setSalePriceMinDraft] = useState('')
  const [salePriceMaxDraft, setSalePriceMaxDraft] = useState('')
  const [appliedFilters, setAppliedFilters] = useState<ProductListFilters>({})
  const [page, setPage] = useState(1)
  const [pagination, setPagination] = useState<PaginationMeta>({ page: 1, page_size: PAGE_SIZE, total: 0, total_pages: 0 })
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [feedback, setFeedback] = useState<{ kind: 'success' | 'error'; message: string } | null>(null)
  const [modal, setModal] = useState<'create' | 'edit' | 'view' | null>(null)
  const [selected, setSelected] = useState<Product | null>(null)
  const [selectedDetails, setSelectedDetails] = useState<Product | null>(null)
  const [detailsLoading, setDetailsLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<Product | null>(null)
  const createButtonCustomization = useCustomizable({ key: 'products.create_button', type: 'BUTTON', group: 'primary-action', page: 'products', label: 'Novo produto' })
  const tableCustomization = useCustomizable({ key: 'products.table', type: 'TABLE', group: 'data-table', page: 'products', label: 'Tabela de produtos' })
  const [deleting, setDeleting] = useState(false)
  const loadRequestId = useRef(0)

  const loadProducts = useCallback(async () => { const requestId = ++loadRequestId.current; setLoading(true); setError(null); try { const [productList, optionList, supplierList] = await Promise.all([listProducts({ ...appliedFilters, page, pageSize: PAGE_SIZE }), listProducts({ page: 1, pageSize: 100 }), listProductSuppliers()]); if (requestId !== loadRequestId.current) return; setProducts(productList); setFilterProducts(optionList); setSuppliers(supplierList); setPagination(getPaginationMeta(productList)) } catch (loadError) { if (requestId === loadRequestId.current) setError(getApiErrorMessage(loadError, 'Não foi possível carregar produtos e fornecedores.')) } finally { if (requestId === loadRequestId.current) setLoading(false) } }, [appliedFilters, page])
  // oxlint-disable-next-line
  useEffect(() => { void loadProducts() }, [loadProducts])

  const hasDraftFilters = Boolean(searchDraft.trim() || categoryDraft.trim() || supplierDraft !== '' || costMinDraft.trim() || costMaxDraft.trim() || salePriceMinDraft.trim() || salePriceMaxDraft.trim())
  const hasAppliedFilters = Boolean(appliedFilters.search || appliedFilters.category || appliedFilters.supplierId || appliedFilters.costMin || appliedFilters.costMax || appliedFilters.salePriceMin || appliedFilters.salePriceMax)
  const filterCategories = uniqueFilterOptions(filterProducts.map((product) => product.categoria))
  const applyFilters = () => { setPage(1); setAppliedFilters({ search: searchDraft.trim(), category: categoryDraft, supplierId: supplierDraft, costMin: costMinDraft.trim(), costMax: costMaxDraft.trim(), salePriceMin: salePriceMinDraft.trim(), salePriceMax: salePriceMaxDraft.trim() }); setFiltersOpen(false) }
  const clearFilters = () => { setPage(1); setSearchDraft(''); setCategoryDraft(''); setSupplierDraft(''); setCostMinDraft(''); setCostMaxDraft(''); setSalePriceMinDraft(''); setSalePriceMaxDraft(''); setAppliedFilters({}); setFiltersOpen(false) }

  const saveProduct = async (payload: ProductPayload) => {
    setSaving(true); setFeedback(null)
    try { const saved = selected ? await updateProduct(selected.id, payload) : await createProduct(payload); setProducts((current) => selected ? current.map((item) => item.id === saved.id ? saved : item) : [...current, saved]); setFilterProducts((current) => selected ? current.map((item) => item.id === saved.id ? saved : item) : [...current, saved]); setModal(null); setSelected(null); setFeedback({ kind: 'success', message: selected ? 'Produto atualizado com sucesso.' : 'Produto criado com sucesso.' }) } catch (saveError) { setFeedback({ kind: 'error', message: getApiErrorMessage(saveError, 'Não foi possível salvar o produto.') }) } finally { setSaving(false) }
  }

  const removeProduct = async () => {
    if (!deleteTarget) return
    setDeleting(true); setFeedback(null)
    try { await deleteProduct(deleteTarget.id); setProducts((current) => current.filter((item) => item.id !== deleteTarget.id)); setFilterProducts((current) => current.filter((item) => item.id !== deleteTarget.id)); setFeedback({ kind: 'success', message: 'Produto excluído com sucesso.' }) } catch (deleteError) { setFeedback({ kind: 'error', message: getApiErrorMessage(deleteError, 'Não é possível excluir este produto porque há itens de venda relacionados.') }) } finally { setDeleting(false); setDeleteTarget(null) }
  }

  const openProductDetails = async (product: Product) => {
    setSelected(product)
    setSelectedDetails(null)
    setDetailsLoading(true)
    setModal('view')
    try {
      setSelectedDetails(await getProduct(product.id))
    } catch (error) {
      setFeedback({ kind: 'error', message: getApiErrorMessage(error, 'Não foi possível carregar os detalhes do produto.') })
    } finally {
      setDetailsLoading(false)
    }
  }

  const supplierName = (supplierId: number) => suppliers.find((supplier) => supplier.id === supplierId)?.nome || 'Fornecedor não encontrado'
  const formValue: ProductPayload = selected
    ? (({ id: _id, campos_personalizados: _custom, ...payload }) => payload)(selected)
    : emptyProduct
  return <div className="crud-page">
    <div className="crud-page-header"><PageHeader eyebrow="Cadastros" title="Produtos" description="Mantenha seu catálogo e seus preços organizados." pageId="products" /><button className="button button-primary" type="button" {...createButtonCustomization} onClick={() => { setSelected(null); setModal('create'); setFeedback(null) }}>+ Novo produto</button></div>
      {feedback ? <FeedbackBanner kind={feedback.kind} message={feedback.message} onDismiss={() => setFeedback(null)} /> : null}
      <section className="filter-toolbar" aria-label="Filtros de produtos">
        <SearchInput value={searchDraft} onChange={setSearchDraft} onSearch={(value) => setAppliedFilters((current) => { const search = value.trim(); if (current.search === search) return current; const { search: _search, ...filters } = current; return search ? { ...filters, search } : filters })} onClear={() => setSearchDraft('')} label="Pesquisar produtos" customizationKey="products.search_input" customizationPage="products" />
        <FilterMenu activeCount={[appliedFilters.category, appliedFilters.supplierId, appliedFilters.costMin, appliedFilters.costMax, appliedFilters.salePriceMin, appliedFilters.salePriceMax].filter(Boolean).length} canClear={hasDraftFilters || hasAppliedFilters} open={filtersOpen} onToggle={() => setFiltersOpen((current) => !current)} onClose={() => setFiltersOpen(false)} onApply={applyFilters} onClear={clearFilters}>
          <label className="filter-field">Categoria<select value={categoryDraft} onChange={(event) => setCategoryDraft(event.target.value)}><option value="">Todas as categorias</option>{filterCategories.map((category) => <option value={category} key={category}>{category}</option>)}</select></label>
          <label className="filter-field">Fornecedor<select value={supplierDraft} onChange={(event) => setSupplierDraft(event.target.value ? Number(event.target.value) : '')}><option value="">Todos os fornecedores</option>{suppliers.map((supplier) => <option value={supplier.id} key={supplier.id}>{supplier.nome}</option>)}</select></label>
          <label className="filter-field">Custo mínimo<input type="number" min="0" step="0.01" value={costMinDraft} onChange={(event) => setCostMinDraft(event.target.value)} /></label>
          <label className="filter-field">Custo máximo<input type="number" min="0" step="0.01" value={costMaxDraft} onChange={(event) => setCostMaxDraft(event.target.value)} /></label>
          <label className="filter-field">Venda mínima<input type="number" min="0" step="0.01" value={salePriceMinDraft} onChange={(event) => setSalePriceMinDraft(event.target.value)} /></label>
          <label className="filter-field">Venda máxima<input type="number" min="0" step="0.01" value={salePriceMaxDraft} onChange={(event) => setSalePriceMaxDraft(event.target.value)} /></label>
        </FilterMenu>
      </section>
      {loading ? <LoadingState label="Carregando produtos..." /> : error ? <ErrorState description={error} onRetry={() => void loadProducts()} /> : products.length === 0 ? <div className="data-card"><EmptyState title={hasAppliedFilters ? 'Nenhum resultado encontrado para os filtros aplicados.' : 'Nenhum produto cadastrado ainda'} description={hasAppliedFilters ? 'Tente ajustar a pesquisa ou limpar os filtros.' : 'Crie um produto e selecione um fornecedor existente.'} /></div> : <><div className="data-card data-table-wrap"><table className="data-table" {...tableCustomization}><thead><tr><th>Produto</th><th>Categoria</th><th>Fornecedor</th><th>Preço de custo</th><th>Preço de venda</th><th><span className="sr-only">Ações</span></th></tr></thead><tbody>{products.map((product) => <tr key={product.id}><td className="data-primary">{product.nome}<span className="data-secondary">ID {product.id}</span></td><td>{product.categoria}</td><td>{supplierName(product.fornecedor_id)}</td><td>{displayMoney(product.preco_custo)}</td><td>{displayMoney(product.preco_venda)}</td><td><div className="table-actions"><button className="table-action" type="button" onClick={() => void openProductDetails(product)}>Ver</button><button className="table-action" type="button" onClick={() => { setSelected(product); setModal('edit') }}>Editar</button><button className="table-action table-action-danger" type="button" onClick={() => setDeleteTarget(product)}>Excluir</button></div></td></tr>)}</tbody></table></div><PaginationControls meta={pagination} onPageChange={setPage} /></>}
    {modal === 'view' && selected ? <Modal title="Detalhes do produto" onClose={() => { setModal(null); setSelectedDetails(null) }}>{detailsLoading ? <LoadingState label="Carregando detalhes do produto..." /> : selectedDetails ? <ProductDetails product={selectedDetails} supplierName={supplierName(selectedDetails.fornecedor_id)} /> : null}</Modal> : null}
    {(modal === 'create' || modal === 'edit') ? <Modal title={modal === 'edit' ? 'Editar produto' : 'Novo produto'} description="Selecione um fornecedor real e informe os valores com precisão." onClose={() => setModal(null)}><ProductForm initialValue={formValue} suppliers={suppliers} saving={saving} onCancel={() => setModal(null)} onSave={(payload) => void saveProduct(payload)} /></Modal> : null}
    {deleteTarget ? <ConfirmDialog title="Excluir produto?" description={`O cadastro de ${deleteTarget.nome} será removido. Itens de venda relacionados impedem a exclusão.`} busy={deleting} onCancel={() => setDeleteTarget(null)} onConfirm={() => void removeProduct()} /> : null}
  </div>
}
