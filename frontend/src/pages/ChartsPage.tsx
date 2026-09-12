import { useState } from 'react'
import { ChartModeSelector, type ChartMode } from '../components/charts/ChartModeSelector'
import { chartMetadata } from '../components/charts/chartMetadata'
import { TelemetryChart } from '../components/charts/TelemetryChart'
import { metricSeries, type TelemetryMetric } from '../components/charts/series'
import { SourceSelector } from '../components/status/SourceSelector'
import { useTelemetryHistory } from '../hooks/useTelemetryHistory'
import { useTelemetryStore, type TelemetrySourceState } from '../stores/telemetryStore'
import type { ProcessedTelemetryV1 } from '../types/telemetry'

const HISTORY_LIMIT = 1_000
const chartMetrics: TelemetryMetric[] = [
  'power_uw',
  'voltage_mv',
  'current_ua',
  'od680',
  'temperature_c',
  'lux',
  'cumulative_energy_mj',
]

const liveWindows: Record<Exclude<ChartMode, 'history'>, number> = {
  'live-60s': 60_000,
  'live-5m': 300_000,
  'live-10m': 600_000,
}

const modeLabels: Record<ChartMode, string> = {
  'live-60s': 'Live 60 s',
  'live-5m': 'Live 5 min',
  'live-10m': 'Live 10 min',
  history: 'Recent stored samples',
}

function selectedSource(
  sources: Record<string, TelemetrySourceState>,
  selectedSourceKey: string | null,
): TelemetrySourceState | null {
  if (selectedSourceKey && sources[selectedSourceKey]) return sources[selectedSourceKey]
  return Object.values(sources)[0] ?? null
}

function selectLiveWindow(frames: ProcessedTelemetryV1[], windowMs: number): ProcessedTelemetryV1[] {
  const latest = frames.at(-1)
  if (!latest) return []

  const latestTimestampMs = Date.parse(latest.timestamp)
  if (!Number.isFinite(latestTimestampMs)) return frames

  const lowerBound = latestTimestampMs - windowMs
  return frames.filter((frame) => {
    const timestampMs = Date.parse(frame.timestamp)
    return Number.isFinite(timestampMs) && timestampMs >= lowerBound
  })
}

function pointsForMetric(frames: ProcessedTelemetryV1[], metric: TelemetryMetric) {
  const points = metricSeries(frames, metric)
  return points.some((point) => point.value !== null) ? points : []
}

export function ChartsPage() {
  const [mode, setMode] = useState<ChartMode>('live-60s')
  const sources = useTelemetryStore((state) => state.sources)
  const selectedSourceKey = useTelemetryStore((state) => state.selectedSource)
  const source = selectedSource(sources, selectedSourceKey)
  const deviceId = source?.latest.device_id ?? null
  const cellId = source?.latest.cell_id ?? null
  const history = useTelemetryHistory(mode === 'history' ? deviceId : null, mode === 'history' ? cellId : null, HISTORY_LIMIT)

  const frames =
    mode === 'history'
      ? history.data
      : source
        ? selectLiveWindow(source.liveBuffer, liveWindows[mode])
        : []

  return (
    <div className="mx-auto max-w-6xl">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-bio-text">Charts</h1>
          <p className="mt-2 text-sm text-bio-muted">Source: <SourceSelector /></p>
          <p className="mt-1 text-sm text-bio-muted">Data mode: {modeLabels[mode]}</p>
        </div>
        <ChartModeSelector mode={mode} onChange={setMode} />
      </div>

      {!source ? (
        <section className="mt-8 rounded-xl border border-dashed border-bio-border bg-bio-panel p-8 text-center">
          <h2 className="text-xl font-semibold text-bio-text">Waiting for BioVolt telemetry</h2>
          <p className="mt-2 text-bio-muted">Connect a device to plot backend-processed measurements.</p>
        </section>
      ) : (
        <>
          {mode === 'history' && history.loading ? <p className="mt-6 text-sm text-bio-muted">Loading stored telemetry…</p> : null}
          {mode === 'history' && history.error ? <p className="mt-6 text-sm text-bio-danger" role="alert">{history.error}</p> : null}
          <section className="mt-6 grid gap-4 md:grid-cols-2">
            {chartMetrics.map((metric) => {
              const metadata = chartMetadata[metric]
              const points = pointsForMetric(frames, metric)
              const emptyMessage = frames.length === 0 ? 'No telemetry samples available for this view.' : `No valid ${metadata.label} data available.`

              return (
                <TelemetryChart
                  emptyMessage={emptyMessage}
                  key={metric}
                  points={points}
                  title={metadata.label}
                  unit={metadata.unit}
                />
              )
            })}
          </section>
        </>
      )}
    </div>
  )
}
