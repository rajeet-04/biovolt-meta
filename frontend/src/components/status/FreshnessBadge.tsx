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
      className={`brutal-tag ${stale ? 'text-bio-warning' : 'text-bio-success'}`}
      role="status"
    >
      <span aria-hidden="true" className={`h-2 w-2 ${stale ? 'bg-bio-warning' : 'bg-bio-success'}`} />
      {stale ? 'Stale' : 'Live'}
    </span>
  )
}
