import { useEffect, useId, useRef } from 'react'

import type { AppearancePageId } from '../features/settings/types'
import { useCustomizable } from '../features/settings/VisualCustomizationContext'
import { actionIcons, iconSizes, iconStroke } from '../app/iconography'

const ClearIcon = actionIcons.searchClear

type SearchInputProps = {
  value: string
  onChange: (value: string) => void
  onClear?: () => void
  onSearch?: (value: string) => void
  debounceMs?: number
  label?: string
  placeholder?: string
  disabled?: boolean
  customizationKey?: string
  customizationPage?: AppearancePageId
}

export function SearchInput({
  value,
  onChange,
  onClear,
  onSearch,
  debounceMs = 300,
  label = 'Pesquisar',
  placeholder = 'Pesquisar...',
  disabled = false,
  customizationKey = 'settings.search_input',
  customizationPage,
}: SearchInputProps) {
  const inputId = useId()
  const onSearchRef = useRef(onSearch)
  const customization = useCustomizable({
    key: customizationKey,
    type: 'INPUT',
    group: 'search-input',
    page: customizationPage,
    label,
  })

  useEffect(() => {
    onSearchRef.current = onSearch
  }, [onSearch])

  useEffect(() => {
    const timeoutId = window.setTimeout(() => onSearchRef.current?.(value), debounceMs)
    return () => window.clearTimeout(timeoutId)
  }, [debounceMs, value])

  return (
    <div className="search-input">
      <label htmlFor={inputId}>{label}</label>
      <div className="search-input-control">
        <input
          id={inputId}
          type="search"
          value={value}
          placeholder={placeholder}
          disabled={disabled}
          {...customization}
          onChange={(event) => onChange(event.target.value)}
        />
        {value ? (
          <button
            className="search-input-clear"
            type="button"
            aria-label="Limpar pesquisa"
            onClick={() => {
              if (onClear) {
                onClear()
                return
              }
              onChange('')
            }}
            disabled={disabled}
          >
            <ClearIcon size={iconSizes.action} stroke={iconStroke} aria-hidden="true" focusable="false" />
          </button>
        ) : null}
      </div>
    </div>
  )
}
