import { actionIcons, iconSizes, iconStroke } from '../app/iconography'
import { useCustomizable } from '../features/settings/VisualCustomizationContext'

const ErrorIcon = actionIcons.alert

type ErrorStateProps = {
  title?: string
  description: string
  onRetry?: () => void
}

export function ErrorState({
  title = 'Não foi possível carregar',
  description,
  onRetry,
}: ErrorStateProps) {
  const rootCustomization = useCustomizable({ key: 'global.error-state', type: 'SURFACE', group: 'system-state', label: title })
  const titleCustomization = useCustomizable({ key: 'global.error-state.title', type: 'TEXT', group: 'system-state', label: title })
  const descriptionCustomization = useCustomizable({ key: 'global.error-state.description', type: 'TEXT', group: 'system-state', label: description })
  const retryCustomization = useCustomizable({ key: 'global.error-state.retry', type: 'BUTTON', group: 'system-state', label: 'Tentar novamente' })
  return (
    <div className="state-card state-card-error" {...rootCustomization} role="alert">
      <span className="state-icon" aria-hidden="true">
        <ErrorIcon size={iconSizes.status} stroke={iconStroke} focusable="false" />
      </span>
      <div>
        <strong {...titleCustomization}>{title}</strong>
        <p {...descriptionCustomization}>{description}</p>
        {onRetry ? (
          <button className="text-button" type="button" {...retryCustomization} onClick={onRetry}>
            Tentar novamente
          </button>
        ) : null}
      </div>
    </div>
  )
}
