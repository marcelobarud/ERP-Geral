// @vitest-environment jsdom

import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { SettingsHubPage } from './SettingsHubPage'
import { settingsHubGroups } from './settingsHub'

afterEach(() => cleanup())

describe('hub de configurações', () => {
  it('renderiza os grupos e destinos definidos pela estrutura de dados', () => {
    render(<SettingsHubPage />)

    expect(screen.getByRole('heading', { name: 'Configurações', level: 1 })).toBeTruthy()
    for (const group of settingsHubGroups) {
      expect(screen.getByRole('heading', { name: group.label, level: 2 })).toBeTruthy()
      for (const destination of group.destinations) {
        expect(screen.getByRole('link', { name: new RegExp(destination.label) })).toHaveProperty('href', expect.stringContaining(destination.path))
      }
    }
  })

  it('mantém descrições e affordance de navegação nos destinos', () => {
    render(<SettingsHubPage />)

    expect(screen.getByText('Escolha quais áreas do ERP ficam disponíveis na navegação.')).toBeTruthy()
    expect(screen.getAllByText('→')).toHaveLength(settingsHubGroups.reduce((total, group) => total + group.destinations.length, 0))
  })

  it('não apresenta Usuários quando a permissão de administração não está disponível', () => {
    render(<SettingsHubPage canManageUsers={false} />)

    expect(screen.queryByRole('link', { name: /Usuários/ })).toBeNull()
  })
})
