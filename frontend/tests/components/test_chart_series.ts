import { describe, expect, it } from 'vitest'
import { metricSeries } from '../../src/components/charts/series'
import type { ProcessedTelemetryV1 } from '../../src/types/telemetry'

function frame(overrides: Partial<ProcessedTelemetryV1> = {}): ProcessedTelemetryV1 {
  return {
    schema_version: 1,
    device_id: 'biovolt-01',
    cell_id: 'cell-a',
    sequence: 12,
    timestamp: '2026-08-24T12:00:00.000Z',
    electrical: {
      voltage_mv: 438.2,
      current_ua: 4.382,
      power_uw: 1.92,
      load_resistance_ohm: 100_000,
      cumulative_energy_mj: 12.34,
    },
    biological: {
      od680: 0.12,
      biomass_g_l: null,
      biomass_total_g: null,
      biomass_delta_g: null,
      co2_biofixed_g: null,
    },
    environment: { temperature_c: 26.4, lux: 910 },
    actuators: { grow_led_pwm: 130, mixer_on: false },
    control: { mode: 'adaptive' },
    ...overrides,
  }
}

describe('metricSeries', () => {
  it('maps an exact backend metric and timestamp to a chart point', () => {
    const points = metricSeries([frame()], 'power_uw')

    expect(points).toEqual([{ timestampMs: Date.parse('2026-08-24T12:00:00.000Z'), value: 1.92 }])
  })

  it('preserves null metric values instead of inventing zeroes', () => {
    const points = metricSeries([frame()], 'od680')

    expect(points).toEqual([{ timestampMs: Date.parse('2026-08-24T12:00:00.000Z'), value: 0.12 }])

    const nullable = frame({ biological: { ...frame().biological, od680: null } })
    expect(metricSeries([nullable], 'od680')).toEqual([
      { timestampMs: Date.parse('2026-08-24T12:00:00.000Z'), value: null },
    ])
  })

  it.each([
    ['voltage_mv', 438.2],
    ['current_ua', 4.382],
    ['power_uw', 1.92],
    ['cumulative_energy_mj', 12.34],
    ['od680', 0.12],
    ['temperature_c', 26.4],
    ['lux', 910],
  ] as const)('selects the backend %s field without transformation', (metric, expected) => {
    const points = metricSeries([frame()], metric)

    expect(points[0]!.value).toBe(expected)
  })

  it('keeps input order when mapping multiple frames', () => {
    const first = frame({ sequence: 1, timestamp: '2026-08-24T12:00:00.000Z' })
    const second = frame({ sequence: 2, timestamp: '2026-08-24T12:00:01.000Z', electrical: { ...first.electrical, power_uw: 2.5 } })

    expect(metricSeries([first, second], 'power_uw')).toEqual([
      { timestampMs: Date.parse(first.timestamp), value: 1.92 },
      { timestampMs: Date.parse(second.timestamp), value: 2.5 },
    ])
  })
})
