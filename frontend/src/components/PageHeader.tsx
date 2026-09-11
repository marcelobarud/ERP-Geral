import type { AppearancePageId } from '../features/settings/types'
import { useCustomizable } from '../features/settings/VisualCustomizationContext'

type PageHeaderProps = {
  eyebrow: string
  title: string
  description: string
  pageId?: AppearancePageId | string
}

export function PageHeader({
  eyebrow,
  title,
  description,
  pageId,
}: PageHeaderProps) {
  const titleCustomization = useCustomizable({
    key: `${pageId ?? 'settings'}.title`,
    type: 'TEXT',
    group: 'page-title',
    page: pageId as AppearancePageId | undefined,
    label: title,
  })

  return (
    <header className="page-header">
      <p className="eyebrow">{eyebrow}</p>
      <h1 {...titleCustomization}>{title}</h1>
      <p className="page-description">{description}</p>
    </header>
  )
}
