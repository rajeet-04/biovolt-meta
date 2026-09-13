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
    <section aria-label="Telemetry status" className="surface mt-6 bg-bio-panel/80 px-4 py-3 md:px-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-bio-muted">Selected source</p>
          <p className="mt-1 text-sm font-medium text-bio-text">
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
        <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 border-t border-bio-border/70 pt-3 text-xs text-bio-muted">
          <time dateTime={frame.timestamp} title={frame.timestamp}>
            Latest telemetry: {formatTimestamp(frame.timestamp)}
          </time>
          <span>Frame {frame.sequence}</span>
          <span>Backend-processed telemetry</span>
        </div>
      ) : (
        <p className="mt-3 border-t border-bio-border/70 pt-3 text-xs text-bio-muted">No frame received from this source.</p>
      )}
    </section>
  )
}
