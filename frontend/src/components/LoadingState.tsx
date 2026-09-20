import { actionIcons, iconSizes, iconStroke } from '../app/iconography'
import { useCustomizable } from '../features/settings/VisualCustomizationContext'

const LoadingIcon = actionIcons.loading

type LoadingStateProps = {
  label?: string
}

export function LoadingState({ label = 'Carregando...' }: LoadingStateProps) {
  const rootCustomization = useCustomizable({ key: 'global.loading-state', type: 'SURFACE', group: 'system-state', label })
  const labelCustomization = useCustomizable({ key: 'global.loading-state.label', type: 'TEXT', group: 'system-state', label })
  return (
    <div className="state-card" {...rootCustomization} role="status" aria-live="polite">
      <span className="state-icon state-icon-loading" aria-hidden="true">
        <LoadingIcon size={iconSizes.status} stroke={iconStroke} focusable="false" />
      </span>
      <div>
        <strong {...labelCustomization}>{label}</strong>
        <p>Estamos preparando as informações para você.</p>
      </div>
    </div>
  )
}
