import { useEffect, useState } from 'react'
import { isTelemetryStale } from '../../lib/stale'

interface FreshnessBadgeProps {
  timestamp: string
  nowMs?: number
  thresholdMs?: number
}

export function FreshnessBadge({ timestamp, nowMs, thresholdMs }: FreshnessBadgeProps) {
  const [clockMs, setClockMs] = useState(() => Date.now())

  useEffect(() => {
    if (nowMs !== undefined) return
    const timer = window.setInterval(() => setClockMs(Date.now()), 250)
    return () => window.clearInterval(timer)
  }, [nowMs])

  const stale = isTelemetryStale(timestamp, nowMs ?? clockMs, thresholdMs)

  return (
    <span
      aria-live="polite"
      className={`inline-flex items-center gap-2 rounded-full border border-bio-border px-2.5 py-1 text-xs font-medium ${stale ? 'text-bio-warning' : 'text-bio-success'}`}
      role="status"
    >
      <span aria-hidden="true" className={`h-1.5 w-1.5 rounded-full ${stale ? 'bg-bio-warning' : 'bg-bio-success'}`} />
      {stale ? 'Stale' : 'Live'}
    </span>
  )
}
