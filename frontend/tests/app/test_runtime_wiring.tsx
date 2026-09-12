import { renderHook, act, render } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  useDashboardSocket,
  type DashboardSocketClientLike,
  type DashboardSocketClientFactory,
} from '../../src/hooks/useDashboardSocket'
import { useSystemStatus } from '../../src/hooks/useSystemStatus'
import { useTelemetryStore } from '../../src/stores/telemetryStore'
import type { ProcessedTelemetryV1 } from '../../src/types/telemetry'

function telemetry(): ProcessedTelemetryV1 {
  return {
    schema_version: 1,
    device_id: 'device-01',
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
      od680: null,
      biomass_g_l: null,
      biomass_total_g: null,
      biomass_delta_g: null,
      co2_biofixed_g: null,
    },
    environment: { temperature_c: 24, lux: null },
    actuators: { grow_led_pwm: 128, mixer_on: false },
    control: { mode: 'monitor' },
  }
}

function statusResponse(): Response {
  return new Response(
    JSON.stringify({
      backend: 'ok',
      database: 'ok',
      connected_devices: ['device-01'],
      device_count: 1,
      devices: {
        'device-01': { latest_telemetry_at: null, latest_telemetry_age_ms: null },
      },
    }),
    { status: 200, headers: { 'content-type': 'application/json' } },
  )
}

function DashboardHarness({ factory }: { factory: DashboardSocketClientFactory }) {
  useDashboardSocket({ clientFactory: factory })
  return null
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

describe('application runtime wiring', () => {
  it('creates and stops exactly one dashboard client for each mounted lifecycle', () => {
    const clients: Array<{
      client: DashboardSocketClientLike
      handlers: Parameters<DashboardSocketClientFactory>[0]
      start: ReturnType<typeof vi.fn>
      stop: ReturnType<typeof vi.fn>
    }> = []
    const factory: DashboardSocketClientFactory = (handlers) => {
      const start = vi.fn()
      const stop = vi.fn()
      const client: DashboardSocketClientLike = {
        start,
        stop,
      }
      clients.push({ client, handlers, start, stop })
      return client
    }

    const first = render(<DashboardHarness factory={factory} />)
    expect(clients).toHaveLength(1)
    expect(clients[0]!.start).toHaveBeenCalledTimes(1)

    act(() => clients[0]!.handlers.onState('connected'))
    act(() => clients[0]!.handlers.onTelemetry(telemetry()))
    act(() => clients[0]!.handlers.onInvalidMessage('bad-payload'))
    expect(useTelemetryStore.getState().wsState).toBe('connected')
    expect(useTelemetryStore.getState().sources['device-01::cell-a']!.latest).toEqual(telemetry())
    expect(useTelemetryStore.getState().lastSocketError).toContain('bad-payload')

    first.unmount()
    expect(clients[0]!.stop).toHaveBeenCalledTimes(1)

    const second = render(<DashboardHarness factory={factory} />)
    expect(clients).toHaveLength(2)
    expect(clients[1]!.start).toHaveBeenCalledTimes(1)
    second.unmount()
    expect(clients[1]!.stop).toHaveBeenCalledTimes(1)
  })

  it('polls status immediately and every five seconds without overlapping requests', async () => {
    vi.useFakeTimers()
    let resolveRequest: ((response: Response) => void) | undefined
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(
      () =>
        new Promise<Response>((resolve) => {
          resolveRequest = resolve
        }),
    )

    const { result, unmount } = renderHook(() => useSystemStatus())
    expect(fetchMock).toHaveBeenCalledTimes(1)

    await act(async () => {
      vi.advanceTimersByTime(5_000)
      await Promise.resolve()
    })
    expect(fetchMock).toHaveBeenCalledTimes(1)

    await act(async () => {
      resolveRequest?.(statusResponse())
      await Promise.resolve()
    })
    expect(result.current.status?.backend).toBe('ok')

    await act(async () => {
      vi.advanceTimersByTime(5_000)
      await Promise.resolve()
    })
    expect(fetchMock).toHaveBeenCalledTimes(2)

    const firstSignal = fetchMock.mock.calls[0]?.[1]
    if (firstSignal === undefined) throw new Error('initial status request was not captured')
    expect(firstSignal.signal).toBeInstanceOf(AbortSignal)
    unmount()
    expect(firstSignal.signal?.aborted).toBe(true)
  })
})
