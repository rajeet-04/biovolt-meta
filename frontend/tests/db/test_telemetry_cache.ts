import { beforeEach, describe, expect, it } from 'vitest'
import { appDb } from '../../src/db/appDb'
import {
  cacheTelemetry,
  loadCachedTelemetry,
  loadSelectedSource,
  saveSelectedSource,
} from '../../src/db/telemetryCache'
import type { ProcessedTelemetryV1 } from '../../src/types/telemetry'

function frame(
  sequence: number,
  timestamp: string,
  deviceId = 'biovolt-01',
  cellId = 'cell-a',
): ProcessedTelemetryV1 {
  return {
    schema_version: 1,
    device_id: deviceId,
    cell_id: cellId,
    sequence,
    timestamp,
    electrical: {
      voltage_mv: 438.2,
      current_ua: 4.382,
      power_uw: 1.92,
      load_resistance_ohm: 100_000,
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
    control: { mode: 'monitor' },
  }
}

beforeEach(async () => {
  await appDb.telemetryCache.clear()
  await appDb.uiState.clear()
})

describe('telemetry cache', () => {
  it('round-trips the exact processed payload and sequence', async () => {
    const telemetry = frame(7, '2026-08-24T12:00:00.000Z')

    await cacheTelemetry(telemetry)
    const rows = await loadCachedTelemetry('biovolt-01::cell-a', 10)

    expect(rows).toHaveLength(1)
    expect(rows[0]!.payload).toEqual(telemetry)
    expect(rows[0]!.sequence).toBe(7)
    expect(rows[0]!.timestamp).toBe(telemetry.timestamp)
    expect(rows[0]!.received_cache_at).toEqual(expect.any(String))
  })

  it('uses a deterministic source-safe key and keeps sources isolated', async () => {
    const telemetry = frame(3, '2026-08-24T12:00:00.000Z', 'device::01', 'cell::a')

    await cacheTelemetry(telemetry)
    const row = await appDb.telemetryCache.toCollection().first()

    expect(row?.key).toBe('device%3A%3A01::cell%3A%3Aa::3::2026-08-24T12:00:00.000Z')
    expect(row?.source_key).toBe('device%3A%3A01::cell%3A%3Aa')
    expect(await loadCachedTelemetry('device::01::cell::a', 10)).toEqual([])
    expect(await loadCachedTelemetry('device%3A%3A01::cell%3A%3Aa', 10)).toHaveLength(1)
  })

  it('returns the newest bounded rows in chronological order', async () => {
    const source = 'biovolt-01::cell-a'
    await cacheTelemetry(frame(1, '2026-08-24T12:00:01.000Z'))
    await cacheTelemetry(frame(3, '2026-08-24T12:00:03.000Z'))
    await cacheTelemetry(frame(2, '2026-08-24T12:00:02.000Z'))
    await cacheTelemetry(frame(4, '2026-08-24T12:00:04.000Z', 'other-device'))

    const rows = await loadCachedTelemetry(source, 2)

    expect(rows.map((row) => row.sequence)).toEqual([2, 3])
  })

  it('persists only the selected source key', async () => {
    await saveSelectedSource('biovolt-01::cell-a')

    expect(await loadSelectedSource()).toBe('biovolt-01::cell-a')
    expect(await appDb.uiState.get('selected_source')).toEqual({
      key: 'selected_source',
      value: 'biovolt-01::cell-a',
    })
  })
})
