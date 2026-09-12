import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  ApiError,
  getLatestTelemetry,
  getSystemStatus,
  getTelemetryHistory,
} from '../../src/lib/api'
import type { ProcessedTelemetryV1 } from '../../src/types/telemetry'

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

function validStatus() {
  return {
    backend: 'ok',
    database: 'ok',
    connected_devices: ['biovolt/01'],
    device_count: 1,
    devices: {
      'biovolt/01': {
        latest_telemetry_at: '2026-08-23T17:30:15Z',
        latest_telemetry_age_ms: 12,
      },
    },
  }
}

function response(body: unknown, init?: ResponseInit): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'content-type': 'application/json' },
    ...init,
  })
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('BioVolt REST API client', () => {
  it('requests system status from a same-origin endpoint and validates it', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(response(validStatus()))

    await expect(getSystemStatus()).resolves.toEqual(validStatus())
    expect(fetchMock).toHaveBeenCalledWith('/api/system/status')
  })

  it('encodes latest telemetry query parameters', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(response(validTelemetry()))

    await getLatestTelemetry('biovolt/01', 'cell A')

    expect(fetchMock).toHaveBeenCalledWith('/api/telemetry/latest?device_id=biovolt%2F01&cell_id=cell+A')
  })

  it('omits the history limit when the caller leaves it undefined', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(response([validTelemetry()]))

    await getTelemetryHistory({ deviceId: 'biovolt/01', cellId: 'cell A' })

    expect(fetchMock).toHaveBeenCalledWith('/api/telemetry/history?device_id=biovolt%2F01&cell_id=cell+A')
  })

  it('includes an explicitly supplied history limit', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(response([validTelemetry()]))

    await getTelemetryHistory({ deviceId: 'biovolt/01', cellId: 'cell A', limit: 25 })

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/telemetry/history?device_id=biovolt%2F01&cell_id=cell+A&limit=25',
    )
  })

  it('passes an abort signal to fetch when provided', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(response(validTelemetry()))
    const controller = new AbortController()

    await getLatestTelemetry('biovolt/01', 'cell A', controller.signal)

    expect(fetchMock).toHaveBeenCalledWith(expect.any(String), { signal: controller.signal })
  })

  it('rejects non-2xx responses with safe JSON detail', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(response({ detail: 'telemetry not found', secret: 'omit' }, { status: 404 }))

    const error = await getLatestTelemetry('biovolt/01', 'cell A').catch((value: unknown) => value)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({
      status: 404,
      path: '/api/telemetry/latest?device_id=biovolt%2F01&cell_id=cell+A',
      detail: 'telemetry not found',
    })
    expect((error as Error).message).not.toContain('secret')
  })

  it('rejects structurally invalid telemetry before returning it', async () => {
    const payload = { ...validTelemetry(), electrical: 'bad' }
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(response(payload))

    await expect(getLatestTelemetry('biovolt/01', 'cell A')).rejects.toMatchObject({
      status: 200,
      detail: 'invalid response payload',
    })
  })

  it('rejects structurally invalid history items before returning them', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(response([{ ...validTelemetry(), sequence: '1' }]))

    await expect(getTelemetryHistory({ deviceId: 'biovolt/01', cellId: 'cell A' })).rejects.toMatchObject({
      detail: 'invalid response payload',
    })
  })
})
