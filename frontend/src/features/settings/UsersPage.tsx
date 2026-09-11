import { useEffect, useMemo, useState, type FormEvent } from 'react'

import { FeedbackBanner } from '../../components/FeedbackBanner'
import { PageHeader } from '../../components/PageHeader'
import { getApiErrorMessage } from '../../services/httpClient'
import { listEmployees } from '../employees/api'
import type { Employee } from '../employees/types'
import { useAuth } from '../auth/AuthContext'
import type { AuthUser, UserRole } from '../auth/api'
import { createUser, listUsers, updateUser, type UserPayload } from './usersApi'

const roleLabels: Record<UserRole, string> = {
  ADMIN: 'Administrador',
  MANAGER: 'Gestor',
  OPERATOR: 'Operador',
}

const emptyForm: UserPayload = {
  nome: '',
  email: '',
  senha: '',
  role: 'OPERATOR',
  funcionario_id: null,
}

export function UsersPage() {
  const { authRequired, user: currentUser } = useAuth()
  const [users, setUsers] = useState<AuthUser[]>([])
  const [employees, setEmployees] = useState<Employee[]>([])
  const [form, setForm] = useState<UserPayload>(emptyForm)
  const [editing, setEditing] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [feedback, setFeedback] = useState<{ kind: 'success' | 'error'; message: string } | null>(null)
  const canManage = !authRequired || currentUser?.role === 'ADMIN'
  const employeeNames = useMemo(() => new Map(employees.map((employee) => [employee.id, employee.nome_completo])), [employees])

  const load = async () => {
    setLoading(true)
    try {
      const [userList, employeeList] = await Promise.all([
        listUsers(),
        listEmployees(false, '', { page: 1, pageSize: 100 }),
      ])
      setUsers(userList)
      setEmployees(employeeList)
    } catch (cause) {
      setFeedback({ kind: 'error', message: getApiErrorMessage(cause, 'Não foi possível carregar os usuários.') })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { void load() }, [])

  const resetForm = () => {
    setEditing(null)
    setForm(emptyForm)
  }

  const beginEdit = (item: AuthUser) => {
    setEditing(item)
    setForm({ nome: item.nome, email: item.email, senha: '', role: item.role, funcionario_id: item.funcionario_id })
    setFeedback(null)
  }

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSaving(true)
    setFeedback(null)
    const payload: UserPayload = { ...form, senha: form.senha?.trim() || undefined }
    try {
      const saved = editing ? await updateUser(editing.id, payload) : await createUser({ ...payload, senha: form.senha })
      setUsers((current) => editing ? current.map((item) => item.id === saved.id ? saved : item) : [...current, saved])
      setFeedback({ kind: 'success', message: editing ? 'Usuário atualizado com sucesso.' : 'Usuário criado com sucesso.' })
      resetForm()
    } catch (cause) {
      setFeedback({ kind: 'error', message: getApiErrorMessage(cause, 'Não foi possível salvar o usuário.') })
    } finally {
      setSaving(false)
    }
  }

  const toggleStatus = async (item: AuthUser) => {
    setFeedback(null)
    try {
      const saved = await updateUser(item.id, { ativo: !item.ativo })
      setUsers((current) => current.map((currentItem) => currentItem.id === saved.id ? saved : currentItem))
      setFeedback({ kind: 'success', message: `Usuário ${saved.ativo ? 'ativado' : 'inativado'}.` })
    } catch (cause) {
      setFeedback({ kind: 'error', message: getApiErrorMessage(cause, 'Não foi possível alterar o status do usuário.') })
    }
  }

  return (
    <div className="settings-page">
      <PageHeader eyebrow="Configurações" title="Usuários" description="Administre acessos, papéis e vínculos com a equipe do ERP." />
      {feedback ? <FeedbackBanner kind={feedback.kind} message={feedback.message} onDismiss={() => setFeedback(null)} /> : null}
      {!canManage ? <FeedbackBanner kind="error" message="Seu papel não permite administrar usuários." /> : null}
      <div className="custom-fields-layout">
        <section className="settings-card">
          <p className="form-help">Os papéis são fixos e as permissões continuam sendo aplicadas pelo backend.</p>
          {loading ? <p className="form-help">Carregando usuários...</p> : users.length === 0 ? <p className="form-help">Nenhum usuário cadastrado.</p> : users.map((item) => (
            <div className="custom-field-row" key={item.id}>
              <div><strong>{item.nome}</strong><span>{item.email} · {roleLabels[item.role]} · {item.funcionario_id ? employeeNames.get(item.funcionario_id) ?? `Funcionário #${item.funcionario_id}` : 'Sem vínculo'}</span></div>
              {canManage ? <div className="table-actions"><button className="table-action" type="button" onClick={() => beginEdit(item)}>Editar</button><button className="button button-secondary" type="button" onClick={() => void toggleStatus(item)}>{item.ativo ? 'Inativar' : 'Ativar'}</button></div> : <span>{item.ativo ? 'Ativo' : 'Inativo'}</span>}
            </div>
          ))}
        </section>
        {canManage ? <form className="settings-card" onSubmit={(event) => void submit(event)}>
          <p className="eyebrow">{editing ? 'Editar usuário' : 'Novo usuário'}</p>
          <h2>{editing ? editing.email : 'Acesso ao ERP'}</h2>
          <div className="form-grid">
            <div className="form-field form-grid-wide"><label htmlFor="user-name">Nome</label><input id="user-name" required minLength={2} value={form.nome} onChange={(event) => setForm((current) => ({ ...current, nome: event.target.value }))} /></div>
            <div className="form-field form-grid-wide"><label htmlFor="user-email">E-mail</label><input id="user-email" required type="email" value={form.email} onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))} /></div>
            <div className="form-field"><label htmlFor="user-role">Papel</label><select id="user-role" value={form.role} onChange={(event) => setForm((current) => ({ ...current, role: event.target.value as UserRole }))}>{Object.entries(roleLabels).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></div>
            <div className="form-field"><label htmlFor="user-employee">Funcionário</label><select id="user-employee" value={form.funcionario_id ?? ''} onChange={(event) => setForm((current) => ({ ...current, funcionario_id: event.target.value ? Number(event.target.value) : null }))}><option value="">Sem vínculo</option>{employees.map((employee) => <option value={employee.id} key={employee.id}>{employee.nome_completo}</option>)}</select></div>
            <div className="form-field form-grid-wide"><label htmlFor="user-password">Senha {editing ? '(deixe em branco para manter)' : ''}</label><input id="user-password" type="password" minLength={12} required={!editing} value={form.senha ?? ''} onChange={(event) => setForm((current) => ({ ...current, senha: event.target.value }))} /></div>
          </div>
          <div className="form-actions">{editing ? <button className="button button-secondary" type="button" onClick={resetForm} disabled={saving}>Cancelar</button> : null}<button className="button button-primary" type="submit" disabled={saving}>{saving ? 'Salvando...' : editing ? 'Salvar usuário' : 'Criar usuário'}</button></div>
        </form> : null}
      </div>
    </div>
  )
}
