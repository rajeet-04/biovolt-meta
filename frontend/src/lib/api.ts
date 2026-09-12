import {
  isProcessedTelemetryV1,
  isRecord,
  type ProcessedTelemetryV1,
} from '../types/telemetry'
import type { DeviceSystemStatus, SystemStatus } from '../types/system'

export interface TelemetryHistoryQuery {
  deviceId: string
  cellId: string
  limit?: number
}

/**
 * Describes an HTTP or response-contract failure from the BioVolt API.
 *
 * The response body is deliberately not retained. Only a JSON string `detail`
 * is exposed so a server cannot accidentally put an arbitrary response body
 * into an error shown by the UI.
 */
export class ApiError extends Error {
  readonly status: number
  readonly path: string
  readonly detail: string | undefined

  constructor(status: number, path: string, detail?: string) {
    const suffix = detail ? `: ${detail}` : ''
    super(`BioVolt API request failed (${status}) ${path}${suffix}`)
    this.name = 'ApiError'
    this.status = status
    this.path = path
    this.detail = detail
  }
}

function appendQuery(path: string, params: Record<string, string | undefined>): string {
  const search = new URLSearchParams()
  for (const [name, value] of Object.entries(params)) {
    if (value !== undefined) search.set(name, value)
  }

  const query = search.toString()
  return query ? `${path}?${query}` : path
}

function isSystemStatusDevice(value: unknown): value is DeviceSystemStatus {
  if (!isRecord(value)) return false

  return (
    (value.latest_telemetry_at === null || typeof value.latest_telemetry_at === 'string') &&
    (value.latest_telemetry_age_ms === null ||
      (typeof value.latest_telemetry_age_ms === 'number' &&
        Number.isFinite(value.latest_telemetry_age_ms) &&
        Number.isInteger(value.latest_telemetry_age_ms) &&
        value.latest_telemetry_age_ms >= 0))
  )
}

/** Runtime validation for the backend's system-status response. */
export function isSystemStatus(value: unknown): value is SystemStatus {
  if (!isRecord(value) || !isRecord(value.devices)) return false

  if (
    value.backend !== 'ok' ||
    (value.database !== 'ok' && value.database !== 'error') ||
    !Array.isArray(value.connected_devices) ||
    !value.connected_devices.every((deviceId): deviceId is string => typeof deviceId === 'string') ||
    typeof value.device_count !== 'number' ||
    !Number.isInteger(value.device_count) ||
    value.device_count < 0
  ) {
    return false
  }

  return Object.values(value.devices).every(isSystemStatusDevice)
}

async function readJson(response: Response, path: string): Promise<unknown> {
  if (!response.ok) {
    let detail: string | undefined
    try {
      const body: unknown = await response.json()
      if (isRecord(body) && typeof body.detail === 'string') detail = body.detail
    } catch {
      // A non-JSON error body is intentionally not surfaced to the caller.
    }
    throw new ApiError(response.status, path, detail)
  }

  try {
    return await response.json()
  } catch {
    throw new ApiError(response.status, path, 'invalid JSON response')
  }
}

async function getJson(path: string, signal?: AbortSignal): Promise<unknown> {
  const response = signal === undefined ? await fetch(path) : await fetch(path, { signal })
  return readJson(response, path)
}

async function getValidated<T>(
  path: string,
  guard: (value: unknown) => value is T,
  signal?: AbortSignal,
): Promise<T> {
  const body = await getJson(path, signal)
  if (!guard(body)) {
    throw new ApiError(200, path, 'invalid response payload')
  }
  return body
}

export async function getSystemStatus(signal?: AbortSignal): Promise<SystemStatus> {
  return getValidated('/api/system/status', isSystemStatus, signal)
}

export async function getLatestTelemetry(
  deviceId: string,
  cellId: string,
  signal?: AbortSignal,
): Promise<ProcessedTelemetryV1> {
  const path = appendQuery('/api/telemetry/latest', {
    device_id: deviceId,
    cell_id: cellId,
  })
  return getValidated(path, isProcessedTelemetryV1, signal)
}

export async function getTelemetryHistory(
  query: TelemetryHistoryQuery,
  signal?: AbortSignal,
): Promise<ProcessedTelemetryV1[]> {
  const path = appendQuery('/api/telemetry/history', {
    device_id: query.deviceId,
    cell_id: query.cellId,
    limit: query.limit === undefined ? undefined : String(query.limit),
  })
  const body = await getJson(path, signal)
  if (!Array.isArray(body) || !body.every(isProcessedTelemetryV1)) {
    throw new ApiError(200, path, 'invalid response payload')
  }
  return body
}
