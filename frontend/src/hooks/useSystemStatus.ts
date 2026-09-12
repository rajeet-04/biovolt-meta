import { useEffect, useState } from 'react'
import { getSystemStatus } from '../lib/api'
import type { SystemStatus } from '../types/system'

const STATUS_POLL_INTERVAL_MS = 5_000

export interface SystemStatusState {
  status: SystemStatus | null
  error: string | null
  loading: boolean
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Unable to load BioVolt system status'
}

/** Poll backend status while the application is mounted and abort on cleanup. */
export function useSystemStatus(): SystemStatusState {
  const [state, setState] = useState<SystemStatusState>({
    status: null,
    error: null,
    loading: true,
  })

  useEffect(() => {
    let active = true
    let inFlight = false
    const controller = new AbortController()

    const poll = async (): Promise<void> => {
      if (!active || inFlight) return
      inFlight = true

      try {
        const status = await getSystemStatus(controller.signal)
        if (active) {
          setState({ status, error: null, loading: false })
        }
      } catch (error) {
        if (active && !(error instanceof DOMException && error.name === 'AbortError')) {
          setState((current) => ({ ...current, error: errorMessage(error), loading: false }))
        }
      } finally {
        inFlight = false
      }
    }

    void poll()
    const interval = window.setInterval(() => void poll(), STATUS_POLL_INTERVAL_MS)

    return () => {
      active = false
      controller.abort()
      window.clearInterval(interval)
    }
  }, [])

  return state
}
