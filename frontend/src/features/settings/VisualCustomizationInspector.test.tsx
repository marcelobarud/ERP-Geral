// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import * as appearanceApi from './api'
import {
  resolveCustomizationCandidate,
  VisualCustomizationProvider,
  useVisualCustomization,
} from './VisualCustomizationContext'

vi.mock('./api', () => ({
  getAppearanceOverrides: vi.fn().mockResolvedValue({ items: [] }),
  updateAppearanceOverride: vi.fn(),
  resetAppearanceOverride: vi.fn(),
}))

function InspectorFixture({ onNavigate = vi.fn() }: { onNavigate?: () => void }) {
  const { start } = useVisualCustomization()
  return <>
    <button type="button" onClick={start}>Ativar inspector</button>
    <main>
      <section className="card" data-testid="auto-surface" style={{ backgroundColor: '#ffffff', border: '1px solid #ddd' }}>
        <p>Texto sem instrumentação</p>
        <button type="button" onClick={onNavigate}>Ação repetida</button>
        <a href="/customers">Abrir clientes</a>
        <span className="status-badge-active" data-testid="auto-badge">Ativo</span>
        <svg role="img" aria-label="Ícone de teste" />
        <select aria-label="Seleção de teste"><option>Uma opção</option></select>
        <textarea aria-label="Texto longo de teste" />
      </section>
      <div role="dialog" aria-label="Detalhes">
        <p>Texto do portal</p>
        <input aria-label="Campo do modal" />
      </div>
      <table>
        <thead><tr><th>Nome</th><th>Status</th></tr></thead>
        <tbody><tr><td>João</td><td>Ativo</td></tr><tr><td>Maria</td><td>Inativo</td></tr></tbody>
      </table>
    </main>
  </>
}

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('inspector visual automático', () => {
  it('classifica textos, superfícies, controles, links, ícones e tabelas sem key explícita', () => {
    render(<VisualCustomizationProvider><InspectorFixture /></VisualCustomizationProvider>)
    const surface = screen.getByTestId('auto-surface')
    const text = screen.getByText('Texto sem instrumentação')
    const button = screen.getByRole('button', { name: 'Ação repetida' })
    const dialogInput = screen.getByRole('textbox', { name: 'Campo do modal' })
    const link = screen.getByRole('link', { name: 'Abrir clientes' })
    const badge = screen.getByTestId('auto-badge')
    const icon = screen.getByRole('img', { name: 'Ícone de teste' })
    const select = screen.getByRole('combobox', { name: 'Seleção de teste' })
    const textarea = screen.getByRole('textbox', { name: 'Texto longo de teste' })
    const table = document.querySelector('table') as HTMLTableElement
    const header = table.querySelector('th') as HTMLElement
    const cell = table.querySelector('td') as HTMLElement

    expect(resolveCustomizationCandidate(text)?.semanticType).toBe('TEXT')
    expect(resolveCustomizationCandidate(surface)?.semanticType).toBe('CARD')
    expect(resolveCustomizationCandidate(button)?.semanticType).toBe('BUTTON')
    expect(resolveCustomizationCandidate(dialogInput)?.semanticType).toBe('INPUT')
    expect(resolveCustomizationCandidate(link)?.semanticType).toBe('LINK')
    expect(resolveCustomizationCandidate(badge)?.semanticType).toBe('BADGE')
    expect(resolveCustomizationCandidate(icon)?.semanticType).toBe('ICON')
    expect(resolveCustomizationCandidate(select)?.semanticType).toBe('SELECT')
    expect(resolveCustomizationCandidate(textarea)?.semanticType).toBe('TEXTAREA')
    expect(resolveCustomizationCandidate(table)?.semanticType).toBe('TABLE')
    expect(resolveCustomizationCandidate(header)?.semanticType).toBe('TABLE_HEADER')
    expect(resolveCustomizationCandidate(cell)?.semanticType).toBe('TABLE_CELL')
    expect(resolveCustomizationCandidate(cell)?.key).not.toContain('nth-child')
  })

  it('seleciona texto sem instrumentação, aplica preview e permite subir para a superfície', () => {
    render(<VisualCustomizationProvider><InspectorFixture /></VisualCustomizationProvider>)
    fireEvent.click(screen.getByRole('button', { name: 'Ativar inspector' }))
    const text = screen.getByText('Texto sem instrumentação')
    fireEvent.click(text)

    expect(screen.getByText('Tipo: Texto')).toBeTruthy()
    const color = screen.getByLabelText('Cor')
    fireEvent.change(color, { target: { value: '#ABCDEF' } })
    expect(text.style.color).toBe('rgb(171, 205, 239)')

    const ancestor = screen.getByRole('button', { name: /Card/ })
    fireEvent.click(ancestor)
    expect(screen.getByText('Tipo: Card')).toBeTruthy()
  })

  it('detecta conteúdo de modal/portal e mantém o modo Navegar funcional', () => {
    const onNavigate = vi.fn()
    render(<VisualCustomizationProvider><InspectorFixture onNavigate={onNavigate} /></VisualCustomizationProvider>)
    const portalText = screen.getByText('Texto do portal')
    expect(resolveCustomizationCandidate(portalText)?.semanticType).toBe('TEXT')

    fireEvent.click(screen.getByRole('button', { name: 'Ativar inspector' }))
    fireEvent.click(screen.getByRole('button', { name: 'Navegar' }))
    fireEvent.click(screen.getByRole('button', { name: 'Ação repetida' }))
    expect(onNavigate).toHaveBeenCalledOnce()
    expect(screen.getByText('Modo Navegar: use o ERP normalmente.')).toBeTruthy()
  })

  it('mantém a mesma chave estrutural para células repetidas da mesma coluna', () => {
    render(<VisualCustomizationProvider><InspectorFixture /></VisualCustomizationProvider>)
    const cells = Array.from(document.querySelectorAll('tbody td:first-child')) as HTMLElement[]
    expect(resolveCustomizationCandidate(cells[0])?.key).toBe(resolveCustomizationCandidate(cells[1])?.key)
    expect(resolveCustomizationCandidate(cells[0])?.key).toContain('column.nome')
  })

  it('ignora a própria barra do editor', () => {
    render(<VisualCustomizationProvider><InspectorFixture /></VisualCustomizationProvider>)
    fireEvent.click(screen.getByRole('button', { name: 'Ativar inspector' }))
    expect(resolveCustomizationCandidate(screen.getByRole('status', { name: 'Personalização visual ativa' }))).toBeNull()
    expect(appearanceApi.updateAppearanceOverride).not.toHaveBeenCalled()
  })
})
