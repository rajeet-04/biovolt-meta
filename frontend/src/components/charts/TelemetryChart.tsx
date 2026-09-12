import { Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { ChartPoint } from './series'

interface TelemetryChartProps {
  title: string
  unit: string
  points: ChartPoint[]
  emptyMessage: string
  live?: boolean
  featured?: boolean
}

const signalColors: Record<string, string> = {
  Power: '#154bff',
  'BPV Voltage': '#007c75',
  Current: '#6d28d9',
  'Cumulative Energy': '#a15700',
  OD680: '#b42318',
  Temperature: '#c2410c',
  Light: '#008a65',
}

export function TelemetryChart({ title, unit, points, emptyMessage, live = false, featured = false }: TelemetryChartProps) {
  const color = signalColors[title] ?? '#154bff'

  return (
    <section className={`chart-panel ${featured ? 'md:col-span-2 xl:col-span-2' : ''}`} aria-label={title}>
      <header className="flex items-start justify-between gap-4 border-b-2 border-bio-border pb-3">
        <div>
          <h2 className="text-lg font-black text-bio-text">{title}</h2>
          <p className="text-sm text-bio-muted">Unit: {unit}</p>
        </div>
        <span className="brutal-tag shrink-0" style={{ color }}>
          {live ? 'Live' : 'Stored'}
        </span>
      </header>
      {points.length === 0 ? <p className="mt-6 text-sm text-bio-muted">{emptyMessage}</p> : <>
        <div className={`mt-3 ${featured ? 'h-64' : 'h-52'}`} data-chart-line="preserves-null-gaps">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={points} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
              <CartesianGrid stroke="#d9dfd7" strokeDasharray="3 3" />
              <XAxis dataKey="timestampMs" hide />
              <YAxis axisLine={{ stroke: '#101718' }} tick={{ fill: '#434e50', fontSize: 11 }} tickLine={{ stroke: '#c5cdc4' }} width={48} />
              <Tooltip
                contentStyle={{ backgroundColor: '#101718', border: '2px solid #101718', borderRadius: 0, color: '#ffffff' }}
                cursor={{ stroke: color, strokeDasharray: '4 4', strokeWidth: 1 }}
                labelFormatter={(value) => new Date(Number(value)).toLocaleTimeString()}
              />
              <Area dataKey="value" fill={color} fillOpacity={0.13} stroke="none" type="monotone" connectNulls={false} />
              <Line type="monotone" dataKey="value" connectNulls={false} dot={false} stroke={color} strokeWidth={featured ? 3 : 2} activeDot={{ r: 4, stroke: '#ffffff', strokeWidth: 2 }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <p className="mt-2 text-xs text-bio-muted">Showing {points.length} samples from {new Date(points[0]!.timestampMs).toLocaleString()} to {new Date(points[points.length - 1]!.timestampMs).toLocaleString()}.</p>
        <p className="text-xs text-bio-muted">Null measurements are shown as gaps.</p>
      </>}
    </section>
  )
}
