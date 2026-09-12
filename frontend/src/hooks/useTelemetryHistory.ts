import { useCallback, useEffect, useState } from 'react'
import { getTelemetryHistory } from '../lib/api'
import type { ProcessedTelemetryV1 } from '../types/telemetry'

const MIN_HISTORY_LIMIT = 1
const MAX_HISTORY_LIMIT = 1_000

export interface TelemetryHistoryState {
  data: ProcessedTelemetryV1[]
  loading: boolean
  error: string | null
  reload(): void
}

function clampLimit(limit: number): number {
  if (Number.isNaN(limit)) return MIN_HISTORY_LIMIT
  if (limit === Number.POSITIVE_INFINITY) return MAX_HISTORY_LIMIT
  if (limit === Number.NEGATIVE_INFINITY) return MIN_HISTORY_LIMIT

  return Math.min(MAX_HISTORY_LIMIT, Math.max(MIN_HISTORY_LIMIT, Math.trunc(limit)))
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Unable to load BioVolt telemetry history'
}

function isAbortError(error: unknown): boolean {
  return error instanceof Error && error.name === 'AbortError'
}

export function useTelemetryHistory(
  deviceId: string | null,
  cellId: string | null,
  limit: number,
): TelemetryHistoryState {
  const [state, setState] = useState<Omit<TelemetryHistoryState, 'reload'>>({
    data: [],
    loading: false,
    error: null,
  })
  const [reloadVersion, setReloadVersion] = useState(0)
  const reload = useCallback(() => setReloadVersion((version) => version + 1), [])

  useEffect(() => {
    let active = true

    if (deviceId === null || cellId === null) {
      queueMicrotask(() => {
        if (active) setState({ data: [], loading: false, error: null })
      })
      return () => {
        active = false
      }
    }

    const controller = new AbortController()
    queueMicrotask(() => {
      if (active) setState((current) => ({ ...current, loading: true, error: null }))
    })

    const load = async (): Promise<void> => {
      try {
        const data = await getTelemetryHistory(
          { deviceId, cellId, limit: clampLimit(limit) },
          controller.signal,
        )
        if (active) setState({ data, loading: false, error: null })
      } catch (error) {
        if (active && !isAbortError(error)) {
          setState({ data: [], loading: false, error: errorMessage(error) })
        }
      }
    }

    void load()
    return () => {
      active = false
      controller.abort()
    }
  }, [cellId, deviceId, limit, reloadVersion])

  return { ...state, reload }
}
