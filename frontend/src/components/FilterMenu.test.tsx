// @vitest-environment jsdom

import { fireEvent, render, screen } from '@testing-library/react'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'

import { FilterMenu } from './FilterMenu'

describe('FilterMenu', () => {
  it('keeps details hidden until opened and closes by toggle, outside click and Escape', () => {
    const onApply = vi.fn()
    const onClear = vi.fn()
    const onClose = vi.fn()
    const onToggle = vi.fn()

    const { rerender } = render(
      <FilterMenu activeCount={2} canClear onApply={onApply} onClear={onClear} onClose={onClose} onToggle={onToggle} open={false}>
        <label>Categoria<select><option>Todos</option><option>Alimentos</option></select></label>
      </FilterMenu>,
    )

    expect(screen.queryByRole('dialog', { name: 'Filtros detalhados' })).toBeNull()
    expect(screen.getByRole('button', { name: 'Filtros (2)' })).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'Filtros (2)' }))
    expect(onToggle).toHaveBeenCalledTimes(1)
    rerender(
      <FilterMenu activeCount={2} canClear onApply={onApply} onClear={onClear} onClose={onClose} onToggle={onToggle} open>
        <label>Categoria<select><option>Todos</option><option>Alimentos</option></select></label>
      </FilterMenu>,
    )
    expect(screen.getByRole('dialog', { name: 'Filtros detalhados' })).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'Filtros (2)' }))
    expect(onToggle).toHaveBeenCalledTimes(2)
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalledTimes(1)
    fireEvent.pointerDown(document.body)
    expect(onClose).toHaveBeenCalledTimes(2)
  })

  it('focuses the first filter and returns focus to the trigger when closed', () => {
    function Harness() {
      const [open, setOpen] = useState(false)

      return (
        <FilterMenu
          activeCount={0}
          canClear={false}
          onApply={() => undefined}
          onClear={() => undefined}
          onClose={() => setOpen(false)}
          onToggle={() => setOpen((current) => !current)}
          open={open}
        >
          <label>Categoria<select aria-label="Categoria"><option>Todos</option></select></label>
        </FilterMenu>
      )
    }

    render(<Harness />)
    const trigger = screen.getByRole('button', { name: 'Filtros' })

    trigger.focus()
    fireEvent.click(trigger)
    const select = screen.getAllByRole('combobox', { name: 'Categoria' }).at(-1)
    expect(document.activeElement).toBe(select)

    fireEvent.keyDown(document, { key: 'Escape' })
    expect(document.activeElement).toBe(trigger)
  })
})
