import { request, requestJson } from '../../services/httpClient'
import type { AuthUser, UserRole } from '../auth/api'

export type UserPayload = {
  nome: string
  email: string
  senha?: string
  role: UserRole
  ativo?: boolean
  funcionario_id?: number | null
}

export function listUsers(): Promise<AuthUser[]> {
  return request<AuthUser[]>('/api/users')
}

export function createUser(payload: UserPayload): Promise<AuthUser> {
  return requestJson<AuthUser>('/api/users', 'POST', payload)
}

export function updateUser(id: number, payload: Partial<UserPayload>): Promise<AuthUser> {
  return requestJson<AuthUser>(`/api/users/${id}`, 'PATCH', payload)
}
