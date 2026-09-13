import { formatNullableNumber } from '../../lib/format'

interface MetricCardProps {
  label: string
  value: number | null
  digits: number
  unit: string
  description?: string
}

export function MetricCard({ label, value, digits, unit, description }: MetricCardProps) {
  const formattedValue = formatNullableNumber(value, digits)

  return (
    <article className="rounded-xl border border-bio-border bg-bio-panel p-4 transition-colors hover:border-bio-panel-raised">
      <p className="text-sm font-medium text-bio-muted">{label}</p>
      <p className="data-value mt-2 text-2xl font-semibold tracking-tight text-bio-text">
        {formattedValue === 'Unavailable' ? formattedValue : `${formattedValue} ${unit}`}
      </p>
      {description ? <p className="mt-2 text-sm text-bio-muted">{description}</p> : null}
    </article>
  )
}
