import { useEffect } from 'react'
import {
  DashboardSocketClient,
  type DashboardSocketHandlers,
} from '../lib/dashboardSocket'
import { useTelemetryStore } from '../stores/telemetryStore'

export interface DashboardSocketClientLike {
  start(): void
  stop(): void
}

export type DashboardSocketClientFactory = (
  handlers: DashboardSocketHandlers,
) => DashboardSocketClientLike

export interface UseDashboardSocketOptions {
  clientFactory?: DashboardSocketClientFactory
}

const defaultClientFactory: DashboardSocketClientFactory = (handlers) =>
  new DashboardSocketClient(handlers)

/** Keep one backend dashboard socket attached to the mounted application. */
export function useDashboardSocket(options: UseDashboardSocketOptions = {}): void {
  const clientFactory = options.clientFactory ?? defaultClientFactory

  useEffect(() => {
    const client = clientFactory({
      onTelemetry: (frame) => {
        useTelemetryStore.getState().ingest(frame)
        useTelemetryStore.getState().setSocketError(null)
      },
      onState: (state) => useTelemetryStore.getState().setWsState(state),
      onInvalidMessage: (raw) =>
        useTelemetryStore.getState().setSocketError(`Invalid dashboard telemetry: ${raw}`),
    })

    client.start()
    return () => client.stop()
  }, [clientFactory])
}
