import { useTelemetryStore, type SourceKey, type TelemetrySourceState } from '../../stores/telemetryStore'

const selectorLabel = 'Telemetry source'

function sourceLabel(source: TelemetrySourceState): string {
  return `${source.latest.device_id} · ${source.latest.cell_id}`
}

export function SourceSelector() {
  const sources = useTelemetryStore((state) => state.sources)
  const selectedSource = useTelemetryStore((state) => state.selectedSource)
  const entries = Object.entries(sources) as Array<[SourceKey, TelemetrySourceState]>

  if (entries.length === 0) {
    return <span aria-label={selectorLabel}>No BioVolt telemetry sources</span>
  }

  if (entries.length === 1) {
    return <span aria-label={selectorLabel}>{sourceLabel(entries[0]![1])}</span>
  }

  const activeSource = selectedSource && sources[selectedSource] ? selectedSource : entries[0]![0]

  return (
    <label className="flex items-center gap-2 text-sm text-bio-muted">
      {selectorLabel}
      <select
        aria-label={selectorLabel}
        className="border-2 border-bio-border bg-bio-panel-strong px-2 py-1 font-semibold text-bio-text"
        value={activeSource}
        onChange={(event) => useTelemetryStore.getState().selectSource(event.target.value as SourceKey)}
      >
        {entries.map(([key, source]) => (
          <option key={key} value={key}>
            {sourceLabel(source)}
          </option>
        ))}
      </select>
    </label>
  )
}
