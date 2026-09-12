import type { ProcessedTelemetryV1 } from '../../types/telemetry'

export type TelemetryMetric =
  | 'voltage_mv'
  | 'current_ua'
  | 'power_uw'
  | 'cumulative_energy_mj'
  | 'od680'
  | 'temperature_c'
  | 'lux'

export interface ChartPoint {
  timestampMs: number
  value: number | null
}

function metricValue(frame: ProcessedTelemetryV1, metric: TelemetryMetric): number | null {
  switch (metric) {
    case 'voltage_mv':
      return frame.electrical.voltage_mv
    case 'current_ua':
      return frame.electrical.current_ua
    case 'power_uw':
      return frame.electrical.power_uw
    case 'cumulative_energy_mj':
      return frame.electrical.cumulative_energy_mj
    case 'od680':
      return frame.biological.od680
    case 'temperature_c':
      return frame.environment.temperature_c
    case 'lux':
      return frame.environment.lux
  }
}

export function metricSeries(frames: ProcessedTelemetryV1[], metric: TelemetryMetric): ChartPoint[] {
  return frames.map((frame) => ({
    timestampMs: Date.parse(frame.timestamp),
    value: metricValue(frame, metric),
  }))
}
