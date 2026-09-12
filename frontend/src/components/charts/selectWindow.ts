import type { ProcessedTelemetryV1 } from '../../types/telemetry'

export function selectTimeWindow(
  frames: ProcessedTelemetryV1[],
  windowMs: number,
): ProcessedTelemetryV1[] {
  if (frames.length === 0) return []

  const latestTimestampMs = frames.reduce((latest, frame) => {
    const timestampMs = Date.parse(frame.timestamp)
    return Number.isFinite(timestampMs) ? Math.max(latest, timestampMs) : latest
  }, Number.NEGATIVE_INFINITY)

  if (!Number.isFinite(latestTimestampMs)) return []

  const durationMs = Number.isNaN(windowMs) ? 0 : Math.max(0, windowMs)
  const lowerBoundMs = latestTimestampMs - durationMs

  return frames.filter((frame) => {
    const timestampMs = Date.parse(frame.timestamp)
    return Number.isFinite(timestampMs) && timestampMs >= lowerBoundMs
  })
}
