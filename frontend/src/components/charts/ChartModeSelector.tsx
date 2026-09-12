export type ChartMode = 'live-60s' | 'live-5m' | 'live-10m' | 'history'

interface ChartModeSelectorProps {
  mode: ChartMode
  onChange: (mode: ChartMode) => void
}

const options: Array<{ label: string; value: ChartMode }> = [
  { label: 'Live 60 s', value: 'live-60s' },
  { label: 'Live 5 min', value: 'live-5m' },
  { label: 'Live 10 min', value: 'live-10m' },
  { label: 'Recent stored samples', value: 'history' },
]

export function ChartModeSelector({ mode, onChange }: ChartModeSelectorProps) {
  return (
    <label className="flex items-center gap-2 text-sm text-bio-muted">
      Data mode
      <select
        aria-label="Chart data mode"
        className="rounded-md border border-bio-border bg-bio-panel px-2 py-1 text-bio-text"
        onChange={(event) => onChange(event.target.value as ChartMode)}
        value={mode}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  )
}
