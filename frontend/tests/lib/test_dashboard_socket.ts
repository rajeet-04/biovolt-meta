import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  DashboardSocketClient,
  dashboardSocketUrl,
  reconnectDelay,
  type DashboardSocketHandlers,
} from '../../src/lib/dashboardSocket'
import type { ProcessedTelemetryV1 } from '../../src/types/telemetry'

class FakeWebSocket {
  static instances: FakeWebSocket[] = []

  readonly url: string
  closed = false
  onopen: (() => void) | null = null
  onclose: (() => void) | null = null
  onmessage: ((event: { data: unknown }) => void) | null = null

  constructor(url: string) {
    this.url = url
    FakeWebSocket.instances.push(this)
  }

  close(): void {
    this.closed = true
    this.onclose?.()
  }

  emitOpen(): void {
    this.onopen?.()
  }

  emitClose(): void {
    this.onclose?.()
  }

  emitMessage(data: unknown): void {
    this.onmessage?.({ data })
  }
}

function validTelemetry(): ProcessedTelemetryV1 {
  return {
    schema_version: 1,
    device_id: 'biovolt/01',
    cell_id: 'cell A',
    sequence: 1,
    timestamp: '2026-08-23T17:30:15.124Z',
    electrical: {
      voltage_mv: 438.2,
      current_ua: 4.382,
      power_uw: 1.92,
      load_resistance_ohm: 100000,
      cumulative_energy_mj: null,
    },
    biological: {
      od680: null,
      biomass_g_l: null,
      biomass_total_g: null,
      biomass_delta_g: null,
      co2_biofixed_g: null,
    },
    environment: { temperature_c: 26.4, lux: 910 },
    actuators: { grow_led_pwm: 130, mixer_on: false },
    control: { mode: 'adaptive' },
  }
}

function handlers(): DashboardSocketHandlers & {
  telemetry: ProcessedTelemetryV1[]
  states: DashboardSocketHandlers['onState'] extends (state: infer T) => void ? T[] : never
  invalid: string[]
} {
  const telemetry: ProcessedTelemetryV1[] = []
  const states: Array<'connecting' | 'connected' | 'disconnected'> = []
  const invalid: string[] = []

  return {
    telemetry,
    states,
    invalid,
    onTelemetry: (frame) => telemetry.push(frame),
    onState: (state) => states.push(state),
    onInvalidMessage: (raw) => invalid.push(raw),
  }
}

describe('dashboard WebSocket client', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    FakeWebSocket.instances = []
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('uses bounded exponential reconnect delays', () => {
    expect([0, 1, 2, 3, 4, 5].map(reconnectDelay)).toEqual([1000, 2000, 4000, 8000, 10000, 10000])
  })

  it('constructs a same-host dashboard URL for both page protocols', () => {
    expect(dashboardSocketUrl({ protocol: 'http:', host: 'dashboard.example:4173' })).toBe(
      'ws://dashboard.example:4173/ws/dashboard',
    )
    expect(dashboardSocketUrl({ protocol: 'https:', host: 'dashboard.example' })).toBe(
      'wss://dashboard.example/ws/dashboard',
    )
  })

  it('rejects malformed or structurally invalid messages without telemetry callbacks', () => {
    const events = handlers()
    const client = new DashboardSocketClient(events, {
      socketFactory: (url) => new FakeWebSocket(url),
      location: { protocol: 'http:', host: 'localhost:5173' },
    })

    client.start()
    const socket = FakeWebSocket.instances[0]!
    socket.emitMessage('{malformed')
    socket.emitMessage(JSON.stringify({ ...validTelemetry(), electrical: 'invalid' }))
    socket.emitMessage(JSON.stringify(validTelemetry()))

    expect(events.invalid).toEqual(['{malformed', JSON.stringify({ ...validTelemetry(), electrical: 'invalid' })])
    expect(events.telemetry).toEqual([validTelemetry()])
    client.stop()
  })

  it('reconnects after close with bounded backoff and never opens parallel sockets', () => {
    const events = handlers()
    const client = new DashboardSocketClient(events, {
      socketFactory: (url) => new FakeWebSocket(url),
      location: { protocol: 'http:', host: 'localhost:5173' },
    })

    client.start()
    client.start()
    expect(FakeWebSocket.instances).toHaveLength(1)
    const first = FakeWebSocket.instances[0]!
    first.emitOpen()
    first.emitClose()
    expect(events.states).toEqual(['connecting', 'connected', 'disconnected'])

    vi.advanceTimersByTime(999)
    expect(FakeWebSocket.instances).toHaveLength(1)
    vi.advanceTimersByTime(1)
    expect(FakeWebSocket.instances).toHaveLength(2)

    const second = FakeWebSocket.instances[1]!
    second.emitClose()
    vi.advanceTimersByTime(1999)
    expect(FakeWebSocket.instances).toHaveLength(2)
    vi.advanceTimersByTime(1)
    expect(FakeWebSocket.instances).toHaveLength(3)

    client.stop()
    expect(FakeWebSocket.instances[2]!.closed).toBe(true)
    vi.advanceTimersByTime(60_000)
    expect(FakeWebSocket.instances).toHaveLength(3)
  })
})
