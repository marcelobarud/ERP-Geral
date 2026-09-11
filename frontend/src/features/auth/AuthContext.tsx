import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'

import { getApiErrorMessage, clearAuthToken, getAuthToken, setAuthToken } from '../../services/httpClient'
import { getAuthConfig, getCurrentUser, login as loginRequest, logout as logoutRequest, type AuthUser } from './api'

type AuthContextValue = {
  loading: boolean
  authRequired: boolean
  user: AuthUser | null
  error: string | null
  login: (email: string, senha: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true)
  const [authRequired, setAuthRequired] = useState(false)
  const [user, setUser] = useState<AuthUser | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    void getAuthConfig()
      .then(async (config) => {
        if (!active) return
        setAuthRequired(config.auth_required)
        const token = getAuthToken()
        if (config.auth_required && token) {
          try {
            setUser(await getCurrentUser())
          } catch {
            clearAuthToken()
          }
        }
      })
      .catch(() => {
        // A backend indisponível não deve impedir a tela de diagnóstico local.
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [])

  const login = useCallback(async (email: string, senha: string) => {
    setError(null)
    try {
      const response = await loginRequest(email, senha)
      setAuthToken(response.access_token)
      setUser(response.usuario)
    } catch (loginError) {
      const message = getApiErrorMessage(loginError, 'Não foi possível entrar no ERP.')
      setError(message)
      throw loginError
    }
  }, [])

  const logout = useCallback(async () => {
    try {
      await logoutRequest()
    } finally {
      clearAuthToken()
      setUser(null)
    }
  }, [])

  const value = useMemo(() => ({ loading, authRequired, user, error, login, logout }), [authRequired, error, loading, login, logout, user])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// oxlint-disable-next-line react/only-export-components
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth deve ser usado dentro de AuthProvider')
  return context
}
