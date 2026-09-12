import { appDb, type CachedTelemetryRow, type UiStateRow } from './appDb'
import type { ProcessedTelemetryV1 } from '../types/telemetry'

const MAX_LOAD_LIMIT = 1_000

function sourceKeyForFrame(frame: ProcessedTelemetryV1): string {
  return `${encodeURIComponent(frame.device_id)}::${encodeURIComponent(frame.cell_id)}`
}

function boundedLimit(limit: number): number {
  if (!Number.isFinite(limit)) return limit === Number.POSITIVE_INFINITY ? MAX_LOAD_LIMIT : 0
  return Math.min(MAX_LOAD_LIMIT, Math.max(0, Math.trunc(limit)))
}

function cacheKey(frame: ProcessedTelemetryV1, sourceKey: string): string {
  return `${sourceKey}::${frame.sequence}::${frame.timestamp}`
}

export async function cacheTelemetry(frame: ProcessedTelemetryV1): Promise<void> {
  const sourceKey = sourceKeyForFrame(frame)
  const row: CachedTelemetryRow = {
    key: cacheKey(frame, sourceKey),
    source_key: sourceKey,
    timestamp: frame.timestamp,
    sequence: frame.sequence,
    received_cache_at: new Date().toISOString(),
    payload: frame,
  }

  await appDb.telemetryCache.put(row)
}

export async function loadCachedTelemetry(sourceKey: string, limit: number): Promise<CachedTelemetryRow[]> {
  const bounded = boundedLimit(limit)
  if (bounded === 0) return []

  const rows = await appDb.telemetryCache.where('source_key').equals(sourceKey).toArray()
  rows.sort((left, right) => {
    const timestampOrder = Date.parse(left.timestamp) - Date.parse(right.timestamp)
    return timestampOrder || left.sequence - right.sequence
  })
  return rows.slice(-bounded)
}

export async function saveSelectedSource(sourceKey: string): Promise<void> {
  const row: UiStateRow = { key: 'selected_source', value: sourceKey }
  await appDb.uiState.put(row)
}

export async function loadSelectedSource(): Promise<string | null> {
  const row = await appDb.uiState.get('selected_source')
  return row?.value ?? null
}
