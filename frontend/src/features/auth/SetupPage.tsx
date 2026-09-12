import { useState, type FormEvent } from 'react'

import { useAuth } from './AuthContext'

export function SetupPage() {
  const { bootstrap, error } = useAuth()
  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [token, setToken] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLoading(true)
    try {
      await bootstrap(nome, email, senha, token)
      window.history.replaceState({}, '', '/')
    } catch {
      // O contexto já expõe a mensagem segura para a interface.
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="setup-title">
        <p className="eyebrow">ERP Geral</p>
        <h1 id="setup-title">Configuração inicial</h1>
        <p className="page-description">Crie o primeiro administrador para liberar o acesso à instalação.</p>
        {error ? <div className="state-card state-card-error" role="alert">{error}</div> : null}
        <form className="auth-form" onSubmit={submit}>
          <label className="form-field"><span>Nome do administrador</span><input value={nome} onChange={(event) => setNome(event.target.value)} required minLength={2} autoComplete="name" /></label>
          <label className="form-field"><span>E-mail</span><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="username" /></label>
          <label className="form-field"><span>Senha</span><input type="password" value={senha} onChange={(event) => setSenha(event.target.value)} required minLength={12} autoComplete="new-password" /></label>
          <label className="form-field"><span>Token de bootstrap</span><input value={token} onChange={(event) => setToken(event.target.value)} placeholder="Informe o token definido no .env" minLength={16} autoComplete="off" /></label>
          <button className="button button-primary" type="submit" disabled={loading}>{loading ? 'Configurando...' : 'Criar administrador'}</button>
        </form>
        <p className="form-hint">Depois do primeiro acesso, revise Aparência e Módulos antes da primeira operação.</p>
      </section>
    </main>
  )
}
