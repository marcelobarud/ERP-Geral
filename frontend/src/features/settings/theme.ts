import type { CSSProperties } from 'react'

import type { AppearanceConfig, PageAppearanceTheme } from './types'

export type ThemeStyle = CSSProperties & Record<`--${string}`, string>

export function appearanceCssVars(appearance: AppearanceConfig): ThemeStyle {
  return {
    '--color-primary': appearance.cor_primaria,
    '--color-secondary': appearance.cor_secundaria,
    '--color-accent': appearance.cor_destaque,
    '--color-background': appearance.cor_fundo,
    '--color-surface': appearance.cor_superficie,
    '--color-text-primary': appearance.cor_texto_primario,
    '--color-text-secondary': appearance.cor_texto_secundario,
    '--color-text-muted': appearance.cor_texto_mudo,
    '--color-heading': appearance.cor_titulo,
    '--color-link': appearance.cor_link,
    '--color-on-primary': appearance.cor_sobre_primaria,
    '--color-on-secondary': appearance.cor_sobre_secundaria,
    '--color-on-accent': appearance.cor_sobre_destaque,
    '--color-table-header-text': appearance.cor_tabela_cabecalho,
    '--color-table-body-text': appearance.cor_tabela_corpo,
    '--color-table-background': appearance.cor_tabela_fundo,
    '--color-table-border': appearance.cor_tabela_borda,
    '--color-danger': appearance.cor_perigo,
    '--color-success': appearance.cor_sucesso,
    '--color-warning': appearance.cor_aviso,
    '--color-surface-soft': '#F8FAFB',
    '--color-blue-soft': '#E5F0F5',
    '--color-success-soft': '#E5F5EE',
    '--color-danger-soft': '#FCECEB',
    '--appearance-primary': appearance.cor_primaria,
    '--appearance-secondary': appearance.cor_secundaria,
    '--appearance-accent': appearance.cor_destaque,
    '--appearance-background': appearance.cor_fundo,
    '--appearance-surface': appearance.cor_superficie,
    '--appearance-text': appearance.cor_texto_primario,
    '--appearance-control-radius': appearance.raio_controle,
    '--appearance-card-radius': appearance.raio_card,
  }
}

export function pageAppearanceCssVars(theme: PageAppearanceTheme): ThemeStyle {
  return {
    '--color-background': theme.cor_fundo,
    '--color-surface': theme.cor_superficie,
    '--color-heading': theme.cor_titulo,
    '--color-text-primary': theme.cor_texto_primario,
    '--color-text-secondary': theme.cor_texto_secundario,
    '--color-text-muted': theme.cor_texto_mudo,
    '--color-accent': theme.cor_destaque,
    '--color-link': theme.cor_link,
  }
}
