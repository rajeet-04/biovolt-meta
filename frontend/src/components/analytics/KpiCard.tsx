import { formatNullableNumber } from '../../lib/format'

export function KpiCard({ label, value, unit, description }: { label: string; value: number | null; unit: string; description?: string }) {
  const rendered = formatNullableNumber(value, 2)
  return <article className="rounded border border-bio-border bg-bio-panel p-4"><p className="text-sm text-bio-muted">{label}</p><p className="mt-2 text-2xl font-semibold text-bio-text">{rendered === 'Unavailable' ? rendered : `${rendered} ${unit}`}</p>{description ? <p className="mt-1 text-xs text-bio-muted">{description}</p> : null}</article>
}
