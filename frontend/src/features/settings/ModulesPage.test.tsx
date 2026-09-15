// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import * as modulesApi from './modulesApi'
import { ModulesPage } from './ModulesPage'

vi.mock('./modulesApi', () => ({ listModules: vi.fn(), updateModule: vi.fn() }))

const modules = [
  { id: 1, codigo: 'commercial', nome: 'Comercial', ativo: true, ordem: 10 },
  { id: 2, codigo: 'inventory', nome: 'Estoque', ativo: false, ordem: 30 },
]

describe('página piloto de módulos', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(modulesApi.listModules).mockResolvedValue(modules)
    vi.mocked(modulesApi.updateModule).mockResolvedValue({ ...modules[0], ativo: false })
  })

  afterEach(() => cleanup())

  it('explica o efeito e o estado atual de cada módulo', async () => {
    render(<ModulesPage />)

    expect(await screen.findByText('Vendas, orçamentos, pedidos e devoluções comerciais.')).toBeTruthy()
    expect(screen.getByText('Ativo')).toBeTruthy()
    expect(screen.getByText('Desativado')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Desativar módulo Comercial' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Ativar módulo Estoque' })).toBeTruthy()
  })

  it('preserva o auto-save individual e comunica o impacto da alteração', async () => {
    render(<ModulesPage />)

    fireEvent.click(await screen.findByRole('button', { name: 'Desativar módulo Comercial' }))

    await waitFor(() => expect(modulesApi.updateModule).toHaveBeenCalledWith('commercial', false))
    expect(await screen.findByText('Módulo Comercial desativado. A navegação foi atualizada.')).toBeTruthy()
  })

  it('mantém o contexto e oferece nova tentativa quando o carregamento falha', async () => {
    vi.mocked(modulesApi.listModules).mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce(modules)
    render(<ModulesPage />)

    expect(await screen.findByRole('alert')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Tentar novamente' }))
    expect(await screen.findByText('Áreas do ERP')).toBeTruthy()
    expect(await screen.findByRole('button', { name: 'Desativar módulo Comercial' })).toBeTruthy()
  })
})
