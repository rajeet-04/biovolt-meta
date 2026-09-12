import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { ChartPoint } from './series'

export function TelemetryChart({ title, unit, points, emptyMessage }: { title: string; unit: string; points: ChartPoint[]; emptyMessage: string }) {
  return <section className="rounded-xl border border-bio-border bg-bio-panel p-4" aria-label={title}>
    <h2 className="text-lg font-semibold text-bio-text">{title}</h2><p className="text-sm text-bio-muted">Unit: {unit}</p>
    {points.length === 0 ? <p className="mt-6 text-sm text-bio-muted">{emptyMessage}</p> : <>
      <div className="mt-3 h-48" data-chart-line="preserves-null-gaps"><ResponsiveContainer width="100%" height="100%"><LineChart data={points}><XAxis dataKey="timestampMs" hide /><YAxis width={40} /><Tooltip /><Line type="monotone" dataKey="value" connectNulls={false} stroke="#38bdf8" dot={false} /></LineChart></ResponsiveContainer></div>
      <p className="mt-2 text-xs text-bio-muted">Showing {points.length} samples from {new Date(points[0]!.timestampMs).toLocaleString()} to {new Date(points[points.length - 1]!.timestampMs).toLocaleString()}.</p><p className="text-xs text-bio-muted">Null measurements are shown as gaps.</p>
    </>}
  </section>
}
