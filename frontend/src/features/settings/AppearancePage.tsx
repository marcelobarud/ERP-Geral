import { useState, type ChangeEvent, type FormEvent } from 'react'

import { FeedbackBanner } from '../../components/FeedbackBanner'
import { PageHeader } from '../../components/PageHeader'
import { getApiErrorMessage } from '../../services/httpClient'
import { useAppearance } from './AppearanceContext'
import { useVisualCustomization } from './VisualCustomizationContext'
import type { AppearanceConfig, AppearancePatch } from './types'

const colorFields: { key: keyof AppearanceConfig; label: string }[] = [
  { key: 'cor_primaria', label: 'Cor principal' },
  { key: 'cor_secundaria', label: 'Cor secundária' },
  { key: 'cor_destaque', label: 'Cor de destaque' },
  { key: 'cor_fundo', label: 'Fundo global' },
  { key: 'cor_superficie', label: 'Superfície e cards' },
]

const labels = [
  ['rotulo_dashboard', 'Rótulo dashboard'],
  ['rotulo_clientes', 'Rótulo clientes'],
  ['rotulo_produtos', 'Rótulo produtos'],
  ['rotulo_funcionarios', 'Rótulo funcionários'],
  ['rotulo_fornecedores', 'Rótulo fornecedores'],
  ['rotulo_vendas', 'Rótulo vendas'],
  ['rotulo_nova_venda', 'Rótulo nova venda'],
] as const

const radiusFields = [
  ['raio_controle', 'Arredondamento de controles'],
  ['raio_card', 'Arredondamento de cards'],
] as const

export function AppearancePage() {
  const { appearance, preview, loading, save, reset, uploadLogo, setPreview } = useAppearance()
  const { active: customizationActive, start: startCustomization } = useVisualCustomization()
  const [form, setForm] = useState(appearance)
  const [saving, setSaving] = useState(false)
  const [feedback, setFeedback] = useState<{ kind: 'success' | 'error'; message: string } | null>(null)

  const updateField = <K extends keyof AppearanceConfig>(key: K, value: AppearanceConfig[K]) => {
    const next = { ...form, [key]: value }
    setForm(next)
    setPreview(next)
  }

  const chooseLogo = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    setSaving(true)
    setFeedback(null)
    try {
      const updated = await uploadLogo(file)
      setForm(updated)
      setFeedback({ kind: 'success', message: 'Logo atualizada com sucesso.' })
    } catch (error) {
      setFeedback({ kind: 'error', message: getApiErrorMessage(error, 'Não foi possível atualizar a logo.') })
    } finally {
      setSaving(false)
    }
  }

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSaving(true)
    setFeedback(null)
    try {
      const patch: AppearancePatch = { ...form }
      delete (patch as Partial<AppearanceConfig>).id
      delete (patch as Partial<AppearanceConfig>).logo_url
      const updated = await save(patch)
      setForm(updated)
      setFeedback({ kind: 'success', message: 'Branding global salvo com sucesso.' })
    } catch (error) {
      setFeedback({ kind: 'error', message: getApiErrorMessage(error, 'Não foi possível salvar a aparência.') })
    } finally {
      setSaving(false)
    }
  }

  const restore = async () => {
    setSaving(true)
    setFeedback(null)
    try {
      const restored = await reset()
      setForm(restored)
      setFeedback({ kind: 'success', message: 'Branding global restaurado.' })
    } catch (error) {
      setFeedback({ kind: 'error', message: getApiErrorMessage(error, 'Não foi possível restaurar a aparência.') })
    } finally {
      setSaving(false)
    }
  }

  return <div className="settings-page">
    <PageHeader eyebrow="Configurações" title="Aparência" description="Configure o branding global ou ative o editor visual para personalizar elementos diretamente na interface." pageId="settings" />
    {feedback ? <FeedbackBanner kind={feedback.kind} message={feedback.message} onDismiss={() => setFeedback(null)} /> : null}
    <div className="settings-layout">
      <form className="settings-card" onSubmit={(event) => void submit(event)}>
        <div className="settings-card-heading"><div><p className="eyebrow">Branding global</p><h2>Identidade do ERP</h2><span className="form-help">Estas opções formam a base visual herdada por toda a aplicação.</span></div></div>
        <div className="form-grid">
          <div className="form-field form-grid-wide"><label htmlFor="appearance-name">Nome do sistema</label><input id="appearance-name" value={form.nome_sistema} onChange={(event) => updateField('nome_sistema', event.target.value)} required /></div>
          <div className="form-field form-grid-wide"><label htmlFor="appearance-logo">Logo (PNG, JPEG ou WEBP até 2 MB)</label><input id="appearance-logo" type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => void chooseLogo(event)} /></div>
          {labels.map(([key, label]) => <div className="form-field" key={key}><label htmlFor={`appearance-${key}`}>{label}</label><input id={`appearance-${key}`} value={form[key]} onChange={(event) => updateField(key, event.target.value)} required /></div>)}
        </div>
        <div className="settings-card-heading settings-heading-spaced"><div><p className="eyebrow">Base visual</p><h2>Cores e formas principais</h2></div></div>
        <div className="appearance-options">{colorFields.map(({ key, label }) => <label className="appearance-color-field" key={key}>{label}<input type="color" value={String(form[key])} onChange={(event) => updateField(key, event.target.value.toUpperCase())} /><code>{String(form[key])}</code></label>)}</div>
        <div className="form-grid appearance-radius-grid">{radiusFields.map(([key, label]) => <div className="form-field" key={key}><label htmlFor={`appearance-${key}`}>{label}</label><input id={`appearance-${key}`} value={form[key]} onChange={(event) => updateField(key, event.target.value)} /></div>)}</div>
        <div className="form-actions"><button className="button button-secondary" type="button" onClick={startCustomization} disabled={customizationActive}>🎨 Ativar modo de personalização visual</button><button className="button button-secondary" type="button" onClick={() => void restore()} disabled={saving}>Restaurar padrão</button><button className="button button-primary" type="submit" disabled={saving || loading}>{saving ? 'Salvando...' : 'Salvar aparência global'}</button></div>
      </form>
      <aside className="appearance-preview-card" aria-label="Prévia da aparência global"><p className="eyebrow">Prévia global</p><div className="appearance-preview-brand"><span className="brand-mark" aria-hidden="true">C</span><strong>{preview.nome_sistema}</strong></div><div className="appearance-preview-surface"><strong>{preview.rotulo_dashboard}</strong><p>Elementos sem override específico herdam esta identidade.</p><button className="button button-primary" type="button">Ação principal</button></div><span className="form-help">Para editar um título, card, botão, campo ou tabela individualmente, ative o modo visual.</span></aside>
    </div>
  </div>
}
