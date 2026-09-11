import { FeaturePlaceholder } from '../components/FeaturePlaceholder'

export function NotFoundPage() {
  return (
    <FeaturePlaceholder
      eyebrow="Navegação"
      title="Página não encontrada"
      description="O endereço informado não corresponde a uma área do ERP."
      emptyTitle="Vamos voltar ao começo"
      emptyDescription="Use o menu lateral para acessar uma área disponível."
      icon="?"
    />
  )
}
