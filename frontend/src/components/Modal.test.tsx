// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { useState } from 'react'
import { afterEach, describe, expect, it } from 'vitest'

import { ConfirmDialog } from './ConfirmDialog'
import { Modal } from './Modal'

afterEach(cleanup)

describe('Modal', () => {
  it('focuses the first form field, traps Tab, locks scroll and restores the opener', () => {
    function Harness() {
      const [open, setOpen] = useState(false)

      return (
        <>
          <button type="button" onClick={() => setOpen(true)}>Abrir modal</button>
          {open ? (
            <Modal title="Editar cliente" onClose={() => setOpen(false)}>
              <label>Nome<input aria-label="Nome" /></label>
              <button type="button">Salvar</button>
            </Modal>
          ) : null}
        </>
      )
    }

    render(<Harness />)
    const opener = screen.getByRole('button', { name: 'Abrir modal' })

    opener.focus()
    fireEvent.click(opener)

    const input = screen.getByRole('textbox', { name: 'Nome' })
    const closeButton = screen.getByRole('button', { name: 'Fechar' })
    const saveButton = screen.getByRole('button', { name: 'Salvar' })
    expect(document.activeElement).toBe(input)
    expect(document.body.style.overflow).toBe('hidden')

    saveButton.focus()
    fireEvent.keyDown(document, { key: 'Tab' })
    expect(document.activeElement).toBe(closeButton)

    closeButton.focus()
    fireEvent.keyDown(document, { key: 'Tab', shiftKey: true })
    expect(document.activeElement).toBe(saveButton)

    fireEvent.click(closeButton)
    expect(document.activeElement).toBe(opener)
    expect(document.body.style.overflow).toBe('')
  })

  it('starts confirmation dialogs on the safe action', () => {
    render(
      <>
        <button type="button">Abrir confirmação</button>
        <ConfirmDialog
          title="Excluir cliente?"
          description="A ação não pode ser desfeita."
          onCancel={() => undefined}
          onConfirm={() => undefined}
        />
      </>,
    )

    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Cancelar' }))
  })

  it('keeps Escape and scroll lock with the topmost nested modal', () => {
    function Harness() {
      const [outerOpen, setOuterOpen] = useState(false)
      const [innerOpen, setInnerOpen] = useState(false)

      return (
        <>
          <button type="button" onClick={() => setOuterOpen(true)}>Abrir principal</button>
          {outerOpen ? (
            <Modal title="Parcelas" onClose={() => setOuterOpen(false)}>
              <button type="button" onClick={() => setInnerOpen(true)}>Abrir liquidação</button>
              {innerOpen ? <Modal title="Liquidação" onClose={() => setInnerOpen(false)}><input aria-label="Valor" /></Modal> : null}
            </Modal>
          ) : null}
        </>
      )
    }

    render(<Harness />)
    const opener = screen.getByRole('button', { name: 'Abrir principal' })
    opener.focus()
    fireEvent.click(opener)
    const innerOpener = screen.getByRole('button', { name: 'Abrir liquidação' })
    innerOpener.focus()
    fireEvent.click(innerOpener)

    expect(document.body.style.overflow).toBe('hidden')
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.queryByRole('textbox', { name: 'Valor' })).toBeNull()
    expect(screen.getByRole('button', { name: 'Abrir liquidação' }) === document.activeElement).toBe(true)
    expect(document.body.style.overflow).toBe('hidden')

    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.queryByRole('dialog', { name: 'Parcelas' })).toBeNull()
    expect(document.activeElement).toBe(opener)
    expect(document.body.style.overflow).toBe('')
  })
})
