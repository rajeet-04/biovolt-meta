import { describe, expect, it } from 'vitest'
import { selectTimeWindow } from '../../src/components/charts/selectWindow'
import type { ProcessedTelemetryV1 } from '../../src/types/telemetry'

const frame = (timestamp: string, sequence: number): ProcessedTelemetryV1 => ({ schema_version: 1, device_id: 'd', cell_id: 'c', sequence, timestamp, electrical: { voltage_mv: 1, current_ua: 1, power_uw: 1, load_resistance_ohm: 1, cumulative_energy_mj: 1 }, biological: { od680: 1, biomass_g_l: null, biomass_total_g: null, biomass_delta_g: null, co2_biofixed_g: null }, environment: { temperature_c: 1, lux: 1 }, actuators: { grow_led_pwm: 1, mixer_on: false }, control: { mode: 'monitor' } })

describe('selectTimeWindow', () => {
  it('retains the exact lower boundary and excludes older frames', () => {
    const frames = [frame('2026-08-24T12:00:00Z', 1), frame('2026-08-24T12:00:05Z', 2), frame('2026-08-24T12:00:10Z', 3)]
    expect(selectTimeWindow(frames, 5_000).map((item) => item.sequence)).toEqual([2, 3])
  })
  it('preserves order without mutating the input', () => {
    const frames = [frame('2026-08-24T12:00:00Z', 1), frame('2026-08-24T12:00:01Z', 2)]
    expect(selectTimeWindow(frames, 1_000)).not.toBe(frames)
    expect(frames.map((item) => item.sequence)).toEqual([1, 2])
  })
})
