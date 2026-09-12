import { act, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { OverviewPage } from '../../src/pages/OverviewPage'
import {
  useDashboardSocket,
  type DashboardSocketClientFactory,
  type DashboardSocketClientLike,
} from '../../src/hooks/useDashboardSocket'
import { useSystemStatus } from '../../src/hooks/useSystemStatus'
import { useTelemetryStore } from '../../src/stores/telemetryStore'
import type { ProcessedTelemetryV1 } from '../../src/types/telemetry'

function telemetry(): ProcessedTelemetryV1 {
  return {
    schema_version: 1,
    device_id: 'biovolt-01',
    cell_id: 'cell-a',
    sequence: 4,
    timestamp: '2026-08-24T12:00:00Z',
    electrical: {
      voltage_mv: 3300,
      current_ua: 120,
      power_uw: 396,
      load_resistance_ohm: 27_500,
      cumulative_energy_mj: null,
    },
    biological: {
      od680: 0.42,
      biomass_g_l: null,
      biomass_total_g: null,
      biomass_delta_g: null,
      co2_biofixed_g: null,
    },
    environment: { temperature_c: 24, lux: 800 },
    actuators: { grow_led_pwm: 128, mixer_on: false },
    control: { mode: 'monitor' },
  }
}

function statusResponse(deviceIds: string[]): Response {
  const devices: Record<string, { latest_telemetry_at: string | null; latest_telemetry_age_ms: number | null }> = {}
  for (const id of deviceIds) {
    devices[id] = { latest_telemetry_at: '2026-08-24T12:00:00Z', latest_telemetry_age_ms: 0 }
  }
  return new Response(
    JSON.stringify({
      backend: 'ok',
      database: 'ok',
      connected_devices: deviceIds,
      device_count: deviceIds.length,
      devices,
    }),
    { status: 200, headers: { 'content-type': 'application/json' } },
  )
}

interface CapturedClient {
  client: DashboardSocketClientLike
  handlers: Parameters<DashboardSocketClientFactory>[0]
  start: ReturnType<typeof vi.fn>
  stop: ReturnType<typeof vi.fn>
}

function makeFactory(clients: CapturedClient[]): DashboardSocketClientFactory {
  return (handlers) => {
    const start = vi.fn()
    const stop = vi.fn()
    const client: DashboardSocketClientLike = { start, stop }
    clients.push({ client, handlers, start, stop })
    return client
  }
}

function DashboardHarness({ factory }: { factory: DashboardSocketClientFactory }) {
  useDashboardSocket({ clientFactory: factory })
  useSystemStatus()
  return <OverviewPage />
}

beforeEach(() => {
  useTelemetryStore.setState({
    sources: {},
    selectedSource: null,
    wsState: 'disconnected',
    lastSocketError: null,
  })
})

afterEach(() => {
  vi.restoreAllMocks()
  vi.useRealTimers()
})

describe('dashboard runtime integration', () => {
  it('mounts, connects, renders an ingested frame, and reports a connected source from system status', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(statusResponse(['biovolt-01']))

    const clients: CapturedClient[] = []
    const view = render(<DashboardHarness factory={makeFactory(clients)} />)

    expect(clients).toHaveLength(1)
    expect(clients[0]!.start).toHaveBeenCalledTimes(1)

    await act(async () => {
      clients[0]!.handlers.onState('connected')
      clients[0]!.handlers.onTelemetry(telemetry())
      await Promise.resolve()
    })

    expect(useTelemetryStore.getState().wsState).toBe('connected')
    expect(screen.getByText('Backend connected')).toBeInTheDocument()
    expect(screen.getByText('3300.0 mV')).toBeInTheDocument()
    expect(screen.getByText('120.00 µA')).toBeInTheDocument()
    expect(screen.getByText('396.00 µW')).toBeInTheDocument()
    expect(screen.getByText('0.42 unitless')).toBeInTheDocument()
    expect(screen.getByText('biovolt-01 · cell-a')).toBeInTheDocument()

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalled()
    })
    expect(fetchMock.mock.calls[0]?.[0]).toBe('/api/system/status')

    view.unmount()
    expect(clients[0]!.stop).toHaveBeenCalledTimes(1)
  })

  it('isolates malformed messages: reports the bad payload but still ingests the next valid frame', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(statusResponse([]))

    const clients: CapturedClient[] = []
    render(<DashboardHarness factory={makeFactory(clients)} />)

    await act(async () => {
      clients[0]!.handlers.onState('connected')
      await Promise.resolve()
    })

    act(() => clients[0]!.handlers.onInvalidMessage('not-json'))
    expect(useTelemetryStore.getState().lastSocketError ?? '').toContain('not-json')
    expect(useTelemetryStore.getState().sources).toEqual({})

    act(() => clients[0]!.handlers.onInvalidMessage('{"schema_version":99}'))
    expect(useTelemetryStore.getState().lastSocketError ?? '').toContain('{"schema_version":99}')
    expect(useTelemetryStore.getState().sources).toEqual({})

    await act(async () => {
      clients[0]!.handlers.onTelemetry(telemetry())
      await Promise.resolve()
    })
    const state = useTelemetryStore.getState()
    expect(state.wsState).toBe('connected')
    expect(state.sources['biovolt-01::cell-a']?.latest).toEqual(telemetry())
  })

  it('preserves the last ingested frame and shows a non-live indicator when the backend disconnects', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(statusResponse([]))

    const clients: CapturedClient[] = []
    render(<DashboardHarness factory={makeFactory(clients)} />)

    await act(async () => {
      clients[0]!.handlers.onState('connected')
      clients[0]!.handlers.onTelemetry(telemetry())
      await Promise.resolve()
    })
    expect(screen.getByText('Backend connected')).toBeInTheDocument()

    await act(async () => {
      clients[0]!.handlers.onState('disconnected')
      await Promise.resolve()
    })

    const state = useTelemetryStore.getState()
    expect(state.wsState).toBe('disconnected')
    expect(state.sources['biovolt-01::cell-a']?.latest).toEqual(telemetry())

    expect(screen.getByText('Backend disconnected')).toBeInTheDocument()
    expect(screen.queryByText('Backend connected')).not.toBeInTheDocument()

    expect(screen.getByText('3300.0 mV')).toBeInTheDocument()
    expect(screen.getByText('0.42 unitless')).toBeInTheDocument()
  })
})
