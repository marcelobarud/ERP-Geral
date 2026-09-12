// @vitest-environment jsdom

import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as authContext from './AuthContext'
import { LoginPage } from './LoginPage'

vi.mock('./AuthContext', () => ({ useAuth: vi.fn() }))

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('sends credentials and exposes authentication errors', async () => {
    const login = vi.fn().mockRejectedValue(new Error('Credenciais inválidas.'))
    vi.mocked(authContext.useAuth).mockReturnValue({
      loading: false,
      authRequired: true,
      bootstrapAvailable: false,
      user: null,
      error: 'Credenciais inválidas.',
      login,
      bootstrap: vi.fn(),
      logout: vi.fn(),
    })

    render(<LoginPage />)
    fireEvent.change(screen.getByLabelText('E-mail'), { target: { value: 'user@erp.local' } })
    fireEvent.change(screen.getByLabelText('Senha'), { target: { value: 'Senha-valida-123' } })
    fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    await waitFor(() => expect(login).toHaveBeenCalledWith('user@erp.local', 'Senha-valida-123'))
    expect(screen.getByRole('alert').textContent).toContain('Credenciais inválidas.')
  })
})
