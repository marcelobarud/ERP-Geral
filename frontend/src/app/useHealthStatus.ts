import { useCallback, useEffect, useState } from 'react'

import { getHealth } from '../services/httpClient'

export type HealthStatus = 'loading' | 'online' | 'degraded' | 'offline'

export function useHealthStatus() {
  const [status, setStatus] = useState<HealthStatus>('loading')

  const loadHealth = useCallback(async () => {
    try {
      const response = await getHealth()
      setStatus(response.status === 'ok' ? 'online' : 'degraded')
    } catch {
      setStatus('offline')
    }
  }, [])

  const retry = useCallback(async () => {
    setStatus('loading')
    await loadHealth()
  }, [loadHealth])

  useEffect(() => {
    // The effect intentionally synchronizes this technical indicator with the API.
    // oxlint-disable-next-line react/set-state-in-effect
    void loadHealth()
  }, [loadHealth])

  return { status, retry }
}
