import { useState } from 'react'
import { isTelemetryStale } from '../../lib/stale'

interface FreshnessBadgeProps {
  timestamp: string
  nowMs?: number
  thresholdMs?: number
}

export function FreshnessBadge({ timestamp, nowMs, thresholdMs }: FreshnessBadgeProps) {
  const [mountedAtMs] = useState(() => Date.now())
  const stale = isTelemetryStale(timestamp, nowMs ?? mountedAtMs, thresholdMs)

  return (
    <span
      aria-live="polite"
      className="inline-flex items-center rounded-full border border-bio-border px-2.5 py-1 text-xs font-medium text-bio-text"
      role="status"
    >
      {stale ? 'Stale' : 'Live'}
    </span>
  )
}
