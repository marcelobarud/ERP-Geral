import { request, requestJson } from '../../services/httpClient'

export type ErpModule = { id: number; codigo: string; nome: string; ativo: boolean; ordem: number }

export function listModules(): Promise<ErpModule[]> { return request<ErpModule[]>('/api/modules') }

export function updateModule(codigo: string, ativo: boolean): Promise<ErpModule> {
  return requestJson<ErpModule>(`/api/modules/${codigo}`, 'PATCH', { ativo })
}
