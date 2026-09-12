import type { ReactNode } from 'react'

interface MetricGridProps {
  children: ReactNode
}

export function MetricGrid({ children }: MetricGridProps) {
  return <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{children}</section>
}
