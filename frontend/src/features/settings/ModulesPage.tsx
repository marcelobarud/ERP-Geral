import { useCallback, useEffect, useState } from 'react'

import { FeedbackBanner } from '../../components/FeedbackBanner'
import { PageHeader } from '../../components/PageHeader'
import { getApiErrorMessage } from '../../services/httpClient'
import { listModules, updateModule, type ErpModule } from './modulesApi'

const moduleDescriptions: Record<string, string> = {
  commercial: 'Vendas, orçamentos, pedidos e devoluções comerciais.',
  purchases: 'Pedidos de compra e recebimentos de mercadorias.',
  inventory: 'Saldos, movimentações, ajustes e inventários.',
  finance: 'Contas, liquidações e fluxo financeiro.',
  reports: 'Indicadores e relatórios consolidados do ERP.',
}

export function ModulesPage() {
  const [modules, setModules] = useState<ErpModule[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<{ kind: 'success' | 'error'; message: string } | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const load = useCallback(async () => {
    setLoading(true)
    setLoadError(null)
    try { setModules(await listModules()) } catch (cause) { setLoadError(getApiErrorMessage(cause, 'Não foi possível carregar os módulos.')) } finally { setLoading(false) }
  }, [])
  useEffect(() => { void load() }, [load])
  const toggle = async (module: ErpModule) => {
    setSaving(module.codigo); setFeedback(null)
    try {
      const saved = await updateModule(module.codigo, !module.ativo)
      setModules((current) => current.map((item) => item.codigo === saved.codigo ? saved : item))
      window.dispatchEvent(new Event('erp-modules-changed'))
      setFeedback({ kind: 'success', message: `Módulo ${saved.nome} ${saved.ativo ? 'ativado' : 'desativado'}. A navegação foi atualizada.` })
    } catch (cause) { setFeedback({ kind: 'error', message: getApiErrorMessage(cause, 'Não foi possível atualizar o módulo.') }) } finally { setSaving(null) }
  }
  return (
    <div className="settings-page settings-pilot-page">
      <PageHeader eyebrow="Configurações" title="Módulos" description="Escolha quais áreas ficam disponíveis na navegação do ERP." />
      {feedback ? <FeedbackBanner kind={feedback.kind} message={feedback.message} onDismiss={() => setFeedback(null)} /> : null}
      <section className="settings-card settings-section">
        <div className="settings-section-heading">
          <div>
            <p className="eyebrow">Disponibilidade</p>
            <h2>Áreas do ERP</h2>
            <p>Ative ou desative áreas completas da navegação. A API continua protegida por autenticação e permissões.</p>
          </div>
        </div>
        {loading ? <div className="settings-list settings-list-loading" aria-label="Carregando módulos">{[1, 2, 3].map((item) => <div className="settings-setting-row settings-loading-row" key={item}><span /><span /></div>)}</div> : loadError ? <div className="settings-inline-error" role="alert"><strong>Não foi possível carregar os módulos.</strong><span>{loadError}</span><button className="button button-secondary" type="button" onClick={() => void load()}>Tentar novamente</button></div> : modules.length === 0 ? <p className="form-help">Nenhum módulo disponível.</p> : <div className="settings-list">{modules.map((module) => <div className="settings-setting-row" key={module.codigo}><div className="settings-setting-copy"><strong>{module.nome}</strong><span>{moduleDescriptions[module.codigo] ?? 'Controla a disponibilidade desta área na navegação do ERP.'}</span></div><div className="settings-setting-control"><span className={`settings-status ${module.ativo ? 'settings-status-active' : 'settings-status-inactive'}`}>{module.ativo ? 'Ativo' : 'Desativado'}</span><button className="button button-secondary" type="button" aria-label={`${module.ativo ? 'Desativar' : 'Ativar'} módulo ${module.nome}`} aria-busy={saving === module.codigo} disabled={saving === module.codigo} onClick={() => void toggle(module)}>{saving === module.codigo ? 'Salvando...' : module.ativo ? 'Desativar' : 'Ativar'}</button></div></div>)}</div>}
      </section>
    </div>
  )
}
