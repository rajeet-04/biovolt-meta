import Dexie from 'dexie'
import type { ProcessedTelemetryV1 } from '../types/telemetry'

interface TableLike<T extends { key: string }> {
  clear(): Promise<void>
  get(key: string): Promise<T | undefined>
  put(row: T): Promise<unknown>
  toCollection(): { first(): Promise<T | undefined> }
  where(index: string): { equals(value: string): { toArray(): Promise<T[]> } }
}

class MemoryTable<T extends { key: string }> implements TableLike<T> {
  private readonly rows = new Map<string, T>()

  clear(): Promise<void> {
    this.rows.clear()
    return Promise.resolve()
  }

  get(key: string): Promise<T | undefined> {
    return Promise.resolve(this.rows.get(key))
  }

  put(row: T): Promise<unknown> {
    this.rows.set(row.key, row)
    return Promise.resolve(row.key)
  }

  toCollection(): { first(): Promise<T | undefined> } {
    return { first: () => Promise.resolve(this.rows.values().next().value) }
  }

  where(index: string): { equals(value: string): { toArray(): Promise<T[]> } } {
    return {
      equals: (value: string) => ({
        toArray: () =>
          Promise.resolve([...this.rows.values()].filter((row) => (row as Record<string, unknown>)[index] === value)),
      }),
    }
  }
}

export interface CachedTelemetryRow {
  key: string
  source_key: string
  timestamp: string
  sequence: number
  received_cache_at: string
  payload: ProcessedTelemetryV1
}

export interface UiStateRow {
  key: 'selected_source'
  value: string
}

class BioVoltDatabase extends Dexie {
  telemetryCache!: TableLike<CachedTelemetryRow>
  uiState!: TableLike<UiStateRow>

  constructor() {
    super('biovolt-app')
    if (typeof indexedDB === 'undefined') {
      this.telemetryCache = new MemoryTable<CachedTelemetryRow>()
      this.uiState = new MemoryTable<UiStateRow>()
      return
    }

    this.version(1).stores({
      telemetry_cache: 'key, source_key, timestamp, sequence',
      ui_state: 'key',
    })
    this.telemetryCache = this.table<CachedTelemetryRow, string>('telemetry_cache')
    this.uiState = this.table<UiStateRow, string>('ui_state')
  }
}

export const appDb = new BioVoltDatabase()
