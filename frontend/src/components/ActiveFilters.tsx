export type ActiveFilterItem = {
  key: string
  label: string
  value: string
}

type ActiveFiltersProps = {
  filters: ActiveFilterItem[]
  onRemove: (key: string) => void
  onClear: () => void
}

export function ActiveFilters({ filters, onRemove, onClear }: ActiveFiltersProps) {
  if (!filters.length) return null

  return (
    <div className="active-filters" aria-label="Filtros ativos">
      <span className="active-filters-label">Filtros ativos</span>
      {filters.map((filter) => (
        <button className="filter-chip" type="button" key={filter.key} onClick={() => onRemove(filter.key)}>
          <span>{filter.label}: {filter.value}</span>
          <span aria-hidden="true">×</span>
          <span className="sr-only">Remover filtro {filter.label}</span>
        </button>
      ))}
      <button className="text-button clear-filters" type="button" onClick={onClear}>Limpar filtros</button>
    </div>
  )
}
