import type { ReactNode } from 'react'

import { EmptyState } from './EmptyState'
import { PageHeader } from './PageHeader'

type FeaturePlaceholderProps = {
  eyebrow: string
  title: string
  description: string
  emptyTitle: string
  emptyDescription: string
  icon: ReactNode
}

export function FeaturePlaceholder({
  eyebrow,
  title,
  description,
  emptyTitle,
  emptyDescription,
  icon,
}: FeaturePlaceholderProps) {
  return (
    <div className="page-content">
      <PageHeader eyebrow={eyebrow} title={title} description={description} />
      <section className="placeholder-card" aria-label={title}>
        <div className="placeholder-icon" aria-hidden="true">
          {icon}
        </div>
        <EmptyState title={emptyTitle} description={emptyDescription} />
      </section>
    </div>
  )
}
