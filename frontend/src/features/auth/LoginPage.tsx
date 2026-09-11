import { useState, type FormEvent } from 'react'

import { useAuth } from './AuthContext'

export function LoginPage() {
  const { error, login } = useAuth()
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLoading(true)
    try {
      await login(email, senha)
    } catch {
      // O contexto já expõe a mensagem para a interface.
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="login-title">
        <p className="eyebrow">ERP Geral</p>
        <h1 id="login-title">Entrar no ERP</h1>
        <p className="page-description">Use suas credenciais para acessar a área administrativa.</p>
        {error ? <div className="state-card state-card-error" role="alert">{error}</div> : null}
        <form className="auth-form" onSubmit={submit}>
          <label className="form-field"><span>E-mail</span><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="username" /></label>
          <label className="form-field"><span>Senha</span><input type="password" value={senha} onChange={(event) => setSenha(event.target.value)} required autoComplete="current-password" /></label>
          <button className="button button-primary" type="submit" disabled={loading}>{loading ? 'Entrando...' : 'Entrar'}</button>
        </form>
      </section>
    </main>
  )
}
