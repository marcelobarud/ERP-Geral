import { actionIcons, iconSizes, iconStroke } from '../app/iconography'
import { useCustomizable } from '../features/settings/VisualCustomizationContext'

const SuccessIcon = actionIcons.success
const ErrorIcon = actionIcons.alert
const CloseIcon = actionIcons.close

type FeedbackBannerProps = {
  kind: 'success' | 'error'
  message: string
  onDismiss?: () => void
}

export function FeedbackBanner({
  kind,
  message,
  onDismiss,
}: FeedbackBannerProps) {
  const rootCustomization = useCustomizable({ key: `global.feedback.${kind}`, type: 'SURFACE', group: 'feedback', label: kind === 'error' ? 'Mensagem de erro' : 'Mensagem de sucesso' })
  const messageCustomization = useCustomizable({ key: `global.feedback.${kind}.message`, type: 'TEXT', group: 'feedback', label: message })
  const dismissCustomization = useCustomizable({ key: `global.feedback.${kind}.dismiss`, type: 'BUTTON', group: 'feedback', label: 'Fechar mensagem' })
  return (
    <div className={`feedback feedback-${kind}`} {...rootCustomization} role={kind === 'error' ? 'alert' : 'status'}>
      <span aria-hidden="true">
        {kind === 'success' ? <SuccessIcon size={iconSizes.status} stroke={iconStroke} focusable="false" /> : <ErrorIcon size={iconSizes.status} stroke={iconStroke} focusable="false" />}
      </span>
      <p {...messageCustomization}>{message}</p>
      {onDismiss ? (
        <button type="button" aria-label="Fechar mensagem" {...dismissCustomization} onClick={onDismiss}>
          <CloseIcon size={iconSizes.action} stroke={iconStroke} aria-hidden="true" focusable="false" />
        </button>
      ) : null}
    </div>
  )
}
