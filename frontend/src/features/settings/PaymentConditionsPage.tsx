import { useEffect, useState, type FormEvent } from 'react'

import { FeedbackBanner } from '../../components/FeedbackBanner'
import { Modal } from '../../components/Modal'
import { PageHeader } from '../../components/PageHeader'
import { getApiErrorMessage } from '../../services/httpClient'
import * as api from '../commercial/api'
import type { PaymentCondition } from '../commercial/types'

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
  return <div className="crud-page"><div className="crud-page-header"><PageHeader eyebrow="Configurações" title="Condições de pagamento" description="Defina as condições usadas nos documentos comerciais." pageId="settings" /><button className="button button-primary" type="button" onClick={() => open()}>+ Nova condição</button></div>{feedback ? <FeedbackBanner kind="success" message={feedback} onDismiss={() => setFeedback(null)} /> : null}{error ? <FeedbackBanner kind="error" message={error} onDismiss={() => setError(null)} /> : null}<div className="data-card data-table-wrap mobile-row-cards payment-conditions-table"><table className="data-table"><thead><tr><th>Código</th><th>Nome</th><th>Descrição</th><th>Status</th><th>Ações</th></tr></thead><tbody>{conditions.map((condition) => <tr key={condition.id}><td data-label="Código">{condition.codigo}</td><td className="data-primary" data-label="Nome">{condition.nome}</td><td data-label="Descrição">{condition.descricao || '—'}</td><td data-label="Status">{condition.ativo ? 'Ativa' : 'Inativa'}</td><td data-label="Ações"><button className="table-action" type="button" onClick={() => open(condition)}>Editar</button><button className="table-action" type="button" onClick={() => void toggle(condition)}>{condition.ativo ? 'Inativar' : 'Ativar'}</button></td></tr>)}</tbody></table></div>{editing ? <Modal title={editing === 'create' ? 'Nova condição' : 'Editar condição'} onClose={() => setEditing(null)}><form onSubmit={save}><label className="form-field"><span>Código</span><input required value={form.codigo} onChange={(event) => setForm({ ...form, codigo: event.target.value })} /></label><label className="form-field"><span>Nome</span><input required value={form.nome} onChange={(event) => setForm({ ...form, nome: event.target.value })} /></label><label className="form-field"><span>Descrição</span><textarea value={form.descricao} onChange={(event) => setForm({ ...form, descricao: event.target.value })} /></label><div className="form-actions"><button className="button button-secondary" type="button" onClick={() => setEditing(null)}>Cancelar</button><button className="button button-primary" type="submit">Salvar condição</button></div></form></Modal> : null}</div>
}
