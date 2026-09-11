export type AppearanceLabels = {
  dashboard: string
  customers: string
  products: string
  employees: string
  suppliers: string
  sales: string
  newSale: string
}

export const appearancePageIds = [
  'dashboard', 'customers', 'products', 'employees',
  'suppliers', 'sales', 'new_sale', 'settings',
] as const

export type AppearancePageId = typeof appearancePageIds[number]

export type PageAppearanceTheme = {
  cor_fundo: string
  cor_superficie: string
  cor_titulo: string
  cor_texto_primario: string
  cor_texto_secundario: string
  cor_texto_mudo: string
  cor_destaque: string
  cor_link: string
}

export type PageAppearanceOverrides = {
  [key in keyof PageAppearanceTheme]: string | null
}

export type PageAppearanceConfig = {
  pagina: AppearancePageId
  overrides: PageAppearanceOverrides
  resolved: PageAppearanceTheme
  inherited: string[]
}

export type AppearanceConfig = {
  id: number
  nome_sistema: string
  logo_url: string | null
  cor_primaria: string
  cor_secundaria: string
  cor_destaque: string
  cor_fundo: string
  cor_superficie: string
  cor_texto: string
  cor_texto_primario: string
  cor_texto_secundario: string
  cor_texto_mudo: string
  cor_titulo: string
  cor_link: string
  cor_sobre_primaria: string
  cor_sobre_secundaria: string
  cor_sobre_destaque: string
  cor_tabela_cabecalho: string
  cor_tabela_corpo: string
  cor_tabela_fundo: string
  cor_tabela_borda: string
  cor_perigo: string
  cor_sucesso: string
  cor_aviso: string
  raio_controle: string
  raio_card: string
  rotulo_dashboard: string
  rotulo_clientes: string
  rotulo_produtos: string
  rotulo_funcionarios: string
  rotulo_fornecedores: string
  rotulo_vendas: string
  rotulo_nova_venda: string
}

export type AppearancePatch = Partial<Omit<AppearanceConfig, 'id' | 'logo_url'>>

export type CustomizationType = 'TEXT' | 'SURFACE' | 'BUTTON' | 'INPUT' | 'TABLE' | 'PAGE'

export type CustomizationPropertyValue = string | number

export type CustomizationProperties = Record<string, CustomizationPropertyValue>

export type AppearanceOverride = {
  id: number
  customization_key: string
  customization_type: CustomizationType
  customization_group: string | null
  pagina: AppearancePageId | null
  properties: CustomizationProperties
}

export type AppearanceOverridePayload = Omit<AppearanceOverride, 'id' | 'customization_key'>

export const defaultAppearance: AppearanceConfig = {
  id: 1,
  nome_sistema: 'ERP Geral',
  logo_url: null,
  cor_primaria: '#487A98',
  cor_secundaria: '#2F5975',
  cor_destaque: '#2F8065',
  cor_fundo: '#EEF4F8',
  cor_superficie: '#FFFFFF',
  cor_texto: '#1E293B',
  cor_texto_primario: '#1E293B',
  cor_texto_secundario: '#4B6575',
  cor_texto_mudo: '#718096',
  cor_titulo: '#1E293B',
  cor_link: '#2F5975',
  cor_sobre_primaria: '#FFFFFF',
  cor_sobre_secundaria: '#2F5975',
  cor_sobre_destaque: '#FFFFFF',
  cor_tabela_cabecalho: '#2F5975',
  cor_tabela_corpo: '#1E293B',
  cor_tabela_fundo: '#FFFFFF',
  cor_tabela_borda: '#DCE7EE',
  cor_perigo: '#B95353',
  cor_sucesso: '#2F8065',
  cor_aviso: '#9A7441',
  raio_controle: '0.75rem',
  raio_card: '1.5rem',
  rotulo_dashboard: 'Dashboard',
  rotulo_clientes: 'Clientes',
  rotulo_produtos: 'Produtos',
  rotulo_funcionarios: 'Funcionários',
  rotulo_fornecedores: 'Fornecedores',
  rotulo_vendas: 'Vendas',
  rotulo_nova_venda: 'Nova venda',
}

export function globalTheme(appearance: AppearanceConfig): PageAppearanceTheme {
  return {
    cor_fundo: appearance.cor_fundo,
    cor_superficie: appearance.cor_superficie,
    cor_titulo: appearance.cor_titulo,
    cor_texto_primario: appearance.cor_texto_primario,
    cor_texto_secundario: appearance.cor_texto_secundario,
    cor_texto_mudo: appearance.cor_texto_mudo,
    cor_destaque: appearance.cor_destaque,
    cor_link: appearance.cor_link,
  }
}

export function pageThemeWithFallback(
  appearance: AppearanceConfig,
  overrides: PageAppearanceOverrides,
): PageAppearanceTheme {
  const fallback = globalTheme(appearance)
  return Object.fromEntries(
    Object.keys(fallback).map((key) => [
      key,
      overrides[key as keyof PageAppearanceTheme]
        ?? fallback[key as keyof PageAppearanceTheme],
    ]),
  ) as PageAppearanceTheme
}

export function pageIdForPath(pathname: string): AppearancePageId {
  const ids: Record<string, AppearancePageId> = {
    '/': 'dashboard',
    '/customers': 'customers',
    '/products': 'products',
    '/employees': 'employees',
    '/suppliers': 'suppliers',
    '/sales': 'sales',
    '/sales/new': 'new_sale',
    '/settings/appearance': 'settings',
    '/settings/custom-fields': 'settings',
  }
  return ids[pathname.replace(/\/$/, '') || '/'] ?? 'settings'
}

export function appearanceLabels(appearance: AppearanceConfig): AppearanceLabels {
  return {
    dashboard: appearance.rotulo_dashboard,
    customers: appearance.rotulo_clientes,
    products: appearance.rotulo_produtos,
    employees: appearance.rotulo_funcionarios,
    suppliers: appearance.rotulo_fornecedores,
    sales: appearance.rotulo_vendas,
    newSale: appearance.rotulo_nova_venda,
  }
}
