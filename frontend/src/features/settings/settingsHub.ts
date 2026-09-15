export type SettingsDestination = {
  path: string
  label: string
  description: string
  requiresPermission?: 'manage_users'
}

export type SettingsGroup = {
  id: string
  label: string
  description: string
  destinations: SettingsDestination[]
}

export const settingsHubGroups: SettingsGroup[] = [
  {
    id: 'product-system',
    label: 'Produto e sistema',
    description: 'Definições que controlam a identidade e as áreas disponíveis do ERP.',
    destinations: [
      { path: '/settings/appearance', label: 'Aparência', description: 'Personalize a identidade visual e os rótulos do sistema.' },
      { path: '/settings/modules', label: 'Módulos', description: 'Escolha quais áreas do ERP ficam disponíveis na navegação.' },
    ],
  },
  {
    id: 'operational-data',
    label: 'Dados operacionais',
    description: 'Estruture informações adicionais usadas nos cadastros do ERP.',
    destinations: [
      { path: '/settings/custom-fields', label: 'Campos personalizados', description: 'Defina campos extras para os cadastros operacionais.' },
    ],
  },
  {
    id: 'access',
    label: 'Acesso',
    description: 'Administre quem pode entrar e operar o sistema.',
    destinations: [
      { path: '/settings/users', label: 'Usuários', description: 'Administre acessos, papéis e vínculos com a equipe.', requiresPermission: 'manage_users' },
    ],
  },
  {
    id: 'commercial',
    label: 'Comercial',
    description: 'Configure parâmetros usados nos fluxos comerciais.',
    destinations: [
      { path: '/settings/payment-conditions', label: 'Condições de pagamento', description: 'Gerencie as condições de pagamento comerciais.' },
    ],
  },
]
