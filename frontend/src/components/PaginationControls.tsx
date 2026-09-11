import type { PaginationMeta } from '../types/pagination'

type PaginationControlsProps = {
  meta: PaginationMeta
  onPageChange: (page: number) => void
}

export function PaginationControls({ meta, onPageChange }: PaginationControlsProps) {
  if (meta.total_pages <= 1) return null

  return (
    <nav className="pagination-controls" aria-label="Paginação">
      <span className="pagination-summary">
        Página {meta.page} de {meta.total_pages} · {meta.total} registros
      </span>
      <div className="pagination-actions">
        <button
          className="button button-secondary"
          type="button"
          onClick={() => onPageChange(meta.page - 1)}
          disabled={meta.page <= 1}
        >
          Anterior
        </button>
        <button
          className="button button-secondary"
          type="button"
          onClick={() => onPageChange(meta.page + 1)}
          disabled={meta.page >= meta.total_pages}
        >
          Próxima
        </button>
      </div>
    </nav>
  )
}
