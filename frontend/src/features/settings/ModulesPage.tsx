import { useCallback, useEffect, useState } from 'react'

import { FeedbackBanner } from '../../components/FeedbackBanner'
import { PageHeader } from '../../components/PageHeader'
import { getApiErrorMessage } from '../../services/httpClient'
import { listModules, updateModule, type ErpModule } from './modulesApi'

export function ModulesPage() {
  const [modules, setModules] = useState<ErpModule[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<{ kind: 'success' | 'error'; message: string } | null>(null)
  const load = useCallback(async () => {
    try { setModules(await listModules()) } catch (cause) { setFeedback({ kind: 'error', message: getApiErrorMessage(cause, 'Não foi possível carregar os módulos.') }) } finally { setLoading(false) }
  }, [])
  useEffect(() => { void load() }, [load])
  const toggle = async (module: ErpModule) => {
    setSaving(module.codigo); setFeedback(null)
    try {
      const saved = await updateModule(module.codigo, !module.ativo)
      setModules((current) => current.map((item) => item.codigo === saved.codigo ? saved : item))
      window.dispatchEvent(new Event('erp-modules-changed'))
      setFeedback({ kind: 'success', message: `Módulo ${saved.ativo ? 'ativado' : 'desativado'}.` })
    } catch (cause) { setFeedback({ kind: 'error', message: getApiErrorMessage(cause, 'Não foi possível atualizar o módulo.') }) } finally { setSaving(null) }
  }
  return <div className="settings-page"><PageHeader eyebrow="Configurações" title="Módulos" description="Escolha quais áreas ficam disponíveis na navegação do ERP." />{feedback ? <FeedbackBanner kind={feedback.kind} message={feedback.message} onDismiss={() => setFeedback(null)} /> : null}<section className="settings-card"><p className="form-help">Desativar um módulo oculta sua navegação e bloqueia o acesso direto às telas. A API continua protegida por autenticação e permissões.</p>{loading ? <p className="form-help">Carregando módulos...</p> : modules.map((module) => <div className="custom-field-row" key={module.codigo}><div><strong>{module.nome}</strong><span>{module.ativo ? 'Ativo na navegação' : 'Desativado'}</span></div><button className="button button-secondary" type="button" disabled={saving === module.codigo} onClick={() => void toggle(module)}>{saving === module.codigo ? 'Salvando...' : module.ativo ? 'Desativar' : 'Ativar'}</button></div>)}</section></div>
}
