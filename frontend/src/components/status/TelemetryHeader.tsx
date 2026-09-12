import { formatTimestamp } from '../../lib/format'
import { ConnectionBadge } from './ConnectionBadge'
import { FreshnessBadge } from './FreshnessBadge'
import { SourceSelector } from './SourceSelector'
import type { ProcessedTelemetryV1 } from '../../types/telemetry'

type ConnectionState = 'connecting' | 'connected' | 'disconnected'

interface TelemetryHeaderProps {
  frame: ProcessedTelemetryV1 | null
  wsState: ConnectionState
  nowMs?: number
}

export function TelemetryHeader({ frame, wsState, nowMs }: TelemetryHeaderProps) {
  return (
    <section aria-label="Telemetry status" className="mt-6 rounded-xl border border-bio-border bg-bio-panel p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-bio-muted">Selected source</p>
          <p className="mt-1 text-sm text-bio-text">
            <SourceSelector />
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ConnectionBadge state={wsState} />
          {frame ? (
            <FreshnessBadge
              timestamp={frame.timestamp}
              {...(nowMs === undefined ? {} : { nowMs })}
            />
          ) : null}
        </div>
      </div>
      {frame ? (
        <time className="mt-3 block text-sm text-bio-muted" dateTime={frame.timestamp} title={frame.timestamp}>
          Latest telemetry: {formatTimestamp(frame.timestamp)}
        </time>
      ) : null}
    </section>
  )
}
