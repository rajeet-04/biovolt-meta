import type { ProcessedTelemetryV1 } from '../../src/types/telemetry'
import { useTelemetryStore } from '../../src/stores/telemetryStore'

function frame(sequence: number, deviceId = 'biovolt-01', cellId = 'cell-a'): ProcessedTelemetryV1 {
  return {
    schema_version: 1,
    device_id: deviceId,
    cell_id: cellId,
    sequence,
    timestamp: `2026-08-24T12:00:${String(sequence % 60).padStart(2, '0')}Z`,
    electrical: {
      voltage_mv: 3300,
      current_ua: 120,
      power_uw: 396,
      load_resistance_ohm: 27_500,
      cumulative_energy_mj: sequence === 0 ? null : sequence * 10,
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

beforeEach(() => {
  useTelemetryStore.setState({
    sources: {},
    selectedSource: null,
    wsState: 'disconnected',
    lastSocketError: null,
  })
})

describe('useTelemetryStore', () => {
  it('stores an ingested frame as the exact latest and first buffer item for its source', () => {
    const telemetry = frame(0)

    useTelemetryStore.getState().ingest(telemetry)

    const source = useTelemetryStore.getState().sources['biovolt-01::cell-a']!
    expect(source.latest).toBe(telemetry)
    expect(source.liveBuffer).toEqual([telemetry])
  })

  it('auto-selects the first source without allowing a later source to steal selection', () => {
    useTelemetryStore.getState().ingest(frame(0, 'first', 'cell-a'))
    expect(useTelemetryStore.getState().selectedSource).toBe('first::cell-a')

    useTelemetryStore.getState().ingest(frame(1, 'second', 'cell-a'))
    expect(useTelemetryStore.getState().selectedSource).toBe('first::cell-a')

    useTelemetryStore.getState().selectSource('second::cell-a')
    expect(useTelemetryStore.getState().selectedSource).toBe('second::cell-a')
  })

  it('keeps source identities distinct when identifiers contain the key separator', () => {
    const first = frame(0, 'device::a', 'cell-b')
    const second = frame(1, 'device', 'a::cell-b')

    useTelemetryStore.getState().ingest(first)
    useTelemetryStore.getState().ingest(second)

    const sources = Object.values(useTelemetryStore.getState().sources)
    expect(sources).toHaveLength(2)
    expect(sources.map((source) => source.latest)).toEqual(expect.arrayContaining([first, second]))
  })

  it('keeps only the newest 1,200 frames for each source', () => {
    for (let sequence = 0; sequence < 1_205; sequence += 1) {
      useTelemetryStore.getState().ingest(frame(sequence))
    }

    const source = useTelemetryStore.getState().sources['biovolt-01::cell-a']!
    expect(source.liveBuffer).toHaveLength(1_200)
    expect(source.liveBuffer[0]!.sequence).toBe(5)
    expect(source.liveBuffer.at(-1)!.sequence).toBe(1_204)
    expect(source.latest.sequence).toBe(1_204)
  })

  it('tracks websocket state and socket errors without changing telemetry', () => {
    const telemetry = frame(0)
    useTelemetryStore.getState().ingest(telemetry)

    useTelemetryStore.getState().setWsState('connected')
    useTelemetryStore.getState().setSocketError('connection lost')

    const state = useTelemetryStore.getState()
    expect(state.wsState).toBe('connected')
    expect(state.lastSocketError).toBe('connection lost')
    expect(state.sources['biovolt-01::cell-a']!.latest).toBe(telemetry)
  })
})
