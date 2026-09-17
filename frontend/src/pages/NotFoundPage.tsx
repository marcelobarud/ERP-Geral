import { navigationIcons, iconSizes, iconStroke } from '../app/iconography'
import { FeaturePlaceholder } from '../components/FeaturePlaceholder'

const AlertIcon = navigationIcons.alert

export function NotFoundPage() {
  return (
    <FeaturePlaceholder
      eyebrow="Navegação"
      title="Página não encontrada"
      description="O endereço informado não corresponde a uma área do ERP."
      emptyTitle="Vamos voltar ao começo"
      emptyDescription="Use o menu lateral para acessar uma área disponível."
      icon={<AlertIcon size={iconSizes.placeholder} stroke={iconStroke} aria-hidden="true" focusable="false" />}
    />
  )
}

export function ModuleDisabledPage() {
  return (
    <FeaturePlaceholder
      eyebrow="Configurações"
      title="Módulo desativado"
      description="Esta área foi desativada na configuração atual do ERP."
      emptyTitle="Área indisponível"
      emptyDescription="Ative o módulo em Configurações, na seção Módulos, para liberar seu acesso."
      icon={<AlertIcon size={iconSizes.placeholder} stroke={iconStroke} aria-hidden="true" focusable="false" />}
    />
  )
}
