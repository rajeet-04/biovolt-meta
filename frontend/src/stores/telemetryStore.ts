import { create } from 'zustand'
import type { ProcessedTelemetryV1 } from '../types/telemetry'

export type SourceKey = `${string}::${string}`

export interface TelemetrySourceState {
  latest: ProcessedTelemetryV1
  liveBuffer: ProcessedTelemetryV1[]
}

export interface TelemetryStoreState {
  sources: Record<SourceKey, TelemetrySourceState>
  selectedSource: SourceKey | null
  wsState: 'connecting' | 'connected' | 'disconnected'
  lastSocketError: string | null
  ingest(frame: ProcessedTelemetryV1): void
  selectSource(source: SourceKey): void
  setWsState(state: TelemetryStoreState['wsState']): void
  setSocketError(error: string | null): void
}

const LIVE_BUFFER_LIMIT = 1_200

function sourceKey(frame: ProcessedTelemetryV1): SourceKey {
  // Keep the readable key for ordinary identifiers while escaping separator
  // characters inside either identifier so the pair remains injective.
  return `${encodeURIComponent(frame.device_id)}::${encodeURIComponent(frame.cell_id)}`
}

export const useTelemetryStore = create<TelemetryStoreState>((set) => ({
  sources: {},
  selectedSource: null,
  wsState: 'disconnected',
  lastSocketError: null,

  ingest: (frame) =>
    set((state) => {
      const key = sourceKey(frame)
      const existing = state.sources[key]
      const liveBuffer = existing ? [...existing.liveBuffer, frame].slice(-LIVE_BUFFER_LIMIT) : [frame]

      return {
        sources: {
          ...state.sources,
          [key]: { latest: frame, liveBuffer },
        },
        selectedSource: state.selectedSource ?? key,
      }
    }),

  selectSource: (source) => set({ selectedSource: source }),

  setWsState: (wsState) => set({ wsState }),

  setSocketError: (lastSocketError) => set({ lastSocketError }),
}))
