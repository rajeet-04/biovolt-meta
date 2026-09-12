import type { ReactNode } from 'react'

export interface TelemetryField {
  label: string
  value: ReactNode
  unit?: string
}

export function TelemetryFieldTable({ groups }: { groups: Array<{ name: string; fields: TelemetryField[] }> }) {
  return (
    <div className="overflow-hidden rounded-xl border border-bio-border bg-bio-panel">
      {groups.map((group) => (
        <section key={group.name} aria-labelledby={`group-${group.name}`}>
          <h2 id={`group-${group.name}`} className="border-b border-bio-border px-4 py-3 text-sm font-semibold text-bio-text">{group.name}</h2>
          <dl className="grid gap-x-6 sm:grid-cols-2">
            {group.fields.map((field) => (
              <div key={field.label} className="flex items-baseline justify-between border-b border-bio-border/60 px-4 py-3 text-sm last:border-b-0">
                <dt className="text-bio-muted">{field.label}</dt>
                <dd className="font-medium text-bio-text">{field.value}{field.unit ? ` ${field.unit}` : ''}</dd>
              </div>
            ))}
          </dl>
        </section>
      ))}
    </div>
  )
}
