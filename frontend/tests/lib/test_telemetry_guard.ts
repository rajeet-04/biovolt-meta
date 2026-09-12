import { describe, expect, it } from 'vitest'
import {
  isProcessedTelemetryV1,
  type ProcessedTelemetryV1,
} from '../../src/types/telemetry'

function validTelemetry(): ProcessedTelemetryV1 {
  return {
    schema_version: 1,
    device_id: 'biovolt-01',
    cell_id: 'cell-a',
    sequence: 1245,
    timestamp: '2026-08-23T17:30:15.124+05:30',
    electrical: {
      voltage_mv: 438.2,
      current_ua: 4.382,
      power_uw: 1.92,
      load_resistance_ohm: 100000,
      cumulative_energy_mj: 8.431,
    },
    biological: {
      od680: 0.823,
      biomass_g_l: 0.424,
      biomass_total_g: 0.106,
      biomass_delta_g: 0.022,
      co2_biofixed_g: 0.0403,
    },
    environment: {
      temperature_c: 26.4,
      lux: 910,
    },
    actuators: {
      grow_led_pwm: 130,
      mixer_on: false,
    },
    control: {
      mode: 'adaptive',
    },
  }
}

describe('isProcessedTelemetryV1', () => {
  it('accepts a complete processed telemetry payload', () => {
    expect(isProcessedTelemetryV1(validTelemetry())).toBe(true)
  })

  it('accepts nullable energy when cumulative energy is unavailable', () => {
    const payload = validTelemetry()
    payload.electrical.cumulative_energy_mj = null

    expect(isProcessedTelemetryV1(payload)).toBe(true)
  })

  it.each([
    ['missing device_id', (payload: Record<string, unknown>) => delete payload.device_id],
    ['missing sequence', (payload: Record<string, unknown>) => delete payload.sequence],
  ])('rejects %s', (_description, remove) => {
    const payload = validTelemetry() as unknown as Record<string, unknown>
    remove(payload)

    expect(isProcessedTelemetryV1(payload)).toBe(false)
  })

  it('rejects a schema version other than one', () => {
    const payload = validTelemetry()
    const invalid = { ...payload, schema_version: 2 }

    expect(isProcessedTelemetryV1(invalid)).toBe(false)
  })

  it('rejects a non-object electrical value', () => {
    const payload = validTelemetry()
    const invalid = { ...payload, electrical: 'unavailable' }

    expect(isProcessedTelemetryV1(invalid)).toBe(false)
  })

  it('rejects string-valued power', () => {
    const payload = validTelemetry()
    const invalid = {
      ...payload,
      electrical: { ...payload.electrical, power_uw: '1.92' },
    }

    expect(isProcessedTelemetryV1(invalid)).toBe(false)
  })

  it.each(['2026-02-29T12:00:00Z', '2026-02-31T12:00:00Z'])('rejects impossible calendar date %s', (timestamp) => {
    expect(isProcessedTelemetryV1({ ...validTelemetry(), timestamp })).toBe(false)
  })

  it('rejects unknown top-level fields', () => {
    expect(isProcessedTelemetryV1({ ...validTelemetry(), unexpected: true })).toBe(false)
  })

  it.each([
    ['negative sequence', { sequence: -1 }],
    ['fractional sequence', { sequence: 1.5 }],
    ['zero load resistance', { electrical: { ...validTelemetry().electrical, load_resistance_ohm: 0 } }],
    ['negative optical value', { biological: { ...validTelemetry().biological, od680: -0.1 } }],
    ['out-of-range PWM', { actuators: { ...validTelemetry().actuators, grow_led_pwm: 256 } }],
  ])('rejects %s', (_description, changes) => {
    expect(isProcessedTelemetryV1({ ...validTelemetry(), ...changes })).toBe(false)
  })
})
