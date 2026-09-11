import { request, requestJson } from '../../services/httpClient'

export type UserRole = 'ADMIN' | 'MANAGER' | 'OPERATOR'

export type AuthUser = {
  id: number
  nome: string
  email: string
  ativo: boolean
  role: UserRole
  funcionario_id: number | null
  created_at: string
  updated_at: string
}

export type AuthConfig = {
  auth_required: boolean
}

type LoginResponse = {
  access_token: string
  token_type: 'bearer'
  expires_at: string
  usuario: AuthUser
}

export function getAuthConfig(): Promise<AuthConfig> {
  return request<AuthConfig>('/api/auth/config')
}

export function login(email: string, senha: string): Promise<LoginResponse> {
  return requestJson<LoginResponse>('/api/auth/login', 'POST', { email, senha })
}

export function getCurrentUser(): Promise<AuthUser> {
  return request<AuthUser>('/api/auth/me')
}

export function logout(): Promise<{ ok: boolean }> {
  return requestJson<{ ok: boolean }>('/api/auth/logout', 'POST', {})
}
