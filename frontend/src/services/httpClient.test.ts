// @vitest-environment jsdom

import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  API_BASE_URL,
  ApiError,
  getApiErrorMessage,
  request,
  resolveBackendAssetUrl,
} from './httpClient'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('cliente HTTP', () => {
  it('preserva a mensagem de um erro HTTP sem convertê-lo em falha de conexão', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Dados inválidos para criação.' }), {
        status: 422,
        headers: { 'Content-Type': 'application/json' },
      }),
    ))

    const error = await request('/api/settings/custom-fields/customers').catch(
      (value: unknown) => value,
    )

    expect(error).toBeInstanceOf(ApiError)
    expect((error as ApiError).status).toBe(422)
    expect(getApiErrorMessage(error, 'Não foi possível conectar ao backend.'))
      .toBe('Dados inválidos para criação.')
  })

  it('usa a mensagem de conexão somente quando não existe resposta HTTP', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')))

    const error = await request('/api/settings/appearance/reset').catch(
      (value: unknown) => value,
    )

    expect(error).toBeInstanceOf(ApiError)
    expect((error as ApiError).status).toBe(0)
    expect(getApiErrorMessage(error, 'fallback')).toBe(
      'Não foi possível conectar ao backend.',
    )
  })

  it('não expõe detalhes técnicos de banco ao usuário', () => {
    expect(getApiErrorMessage(new ApiError(500, 'IntegrityError: foreign key violation'), 'Falha segura.')).toBe('Falha segura.')
  })

  it('distingue uma sessão inválida de uma falha de validação', () => {
    expect(getApiErrorMessage(new ApiError(401, 'Autenticação necessária.'), 'fallback')).toContain('sessão')
    expect(getApiErrorMessage(new ApiError(422, 'Quantidade inválida.'), 'fallback')).toBe('Quantidade inválida.')
  })
})

describe('recursos públicos do backend', () => {
  it('resolve caminhos relativos da API no host do backend', () => {
    expect(resolveBackendAssetUrl('/uploads/branding/logo.png')).toBe(
      `${API_BASE_URL}/uploads/branding/logo.png`,
    )
    expect(resolveBackendAssetUrl('uploads/branding/logo.png')).toBe(
      `${API_BASE_URL}/uploads/branding/logo.png`,
    )
  })

  it('preserva URLs absolutas e o fallback vazio', () => {
    expect(resolveBackendAssetUrl('https://cdn.example.com/logo.png')).toBe(
      'https://cdn.example.com/logo.png',
    )
    expect(resolveBackendAssetUrl(null)).toBeNull()
  })
})
