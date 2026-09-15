import { PageHeader } from '../../components/PageHeader'
import { settingsHubGroups } from './settingsHub'

export function SettingsHubPage({ canManageUsers = true }: { canManageUsers?: boolean }) {
  const visibleGroups = settingsHubGroups
    .map((group) => ({
      ...group,
      destinations: group.destinations.filter((destination) => !destination.requiresPermission || canManageUsers),
    }))
    .filter((group) => group.destinations.length > 0)

  return (
    <div className="settings-page settings-hub-page">
      <PageHeader eyebrow="Configurações" title="Configurações" description="Encontre as definições do ERP organizadas por finalidade." />
      <div className="settings-hub-groups">
        {visibleGroups.map((group) => (
          <section className="settings-hub-group" key={group.id}>
            <div className="settings-hub-group-heading">
              <h2>{group.label}</h2>
              <p>{group.description}</p>
            </div>
            <nav className="settings-destination-list" aria-label={group.label}>
              {group.destinations.map((destination) => (
                <a className="settings-destination" href={destination.path} key={destination.path}>
                  <span className="settings-destination-copy">
                    <strong>{destination.label}</strong>
                    <span>{destination.description}</span>
                  </span>
                  <span className="settings-destination-arrow" aria-hidden="true">→</span>
                </a>
              ))}
            </nav>
          </section>
        ))}
      </div>
    </div>
  )
}
