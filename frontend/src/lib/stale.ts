const DEFAULT_STALE_THRESHOLD_MS = 3_000

export function telemetryAgeMs(timestamp: string, nowMs: number): number {
  const timestampMs = Date.parse(timestamp)
  if (Number.isNaN(timestampMs)) {
    return Number.POSITIVE_INFINITY
  }

  return Math.max(0, nowMs - timestampMs)
}

export function isTelemetryStale(
  timestamp: string,
  nowMs: number,
  thresholdMs = DEFAULT_STALE_THRESHOLD_MS,
): boolean {
  return telemetryAgeMs(timestamp, nowMs) > thresholdMs
}
