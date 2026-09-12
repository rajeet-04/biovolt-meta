import { MetricCard } from '../components/metrics/MetricCard'
import { MetricGrid } from '../components/metrics/MetricGrid'
import { TelemetryHeader } from '../components/status/TelemetryHeader'
import { formatMode } from '../lib/format'
import { useTelemetryStore, type TelemetrySourceState } from '../stores/telemetryStore'
import type { ProcessedTelemetryV1 } from '../types/telemetry'

function latestFrame(sources: Record<string, TelemetrySourceState>, selectedSource: string | null): ProcessedTelemetryV1 | null {
  if (selectedSource && sources[selectedSource]) {
    return sources[selectedSource].latest
  }

  return Object.values(sources)[0]?.latest ?? null
}

export function OverviewPage() {
  const sources = useTelemetryStore((state) => state.sources)
  const selectedSource = useTelemetryStore((state) => state.selectedSource)
  const wsState = useTelemetryStore((state) => state.wsState)
  const frame = latestFrame(sources, selectedSource)

  if (!frame) {
    return (
      <div className="mx-auto max-w-5xl">
        <h1 className="text-3xl font-semibold tracking-tight text-bio-text">Overview</h1>
        <TelemetryHeader frame={null} wsState={wsState} />
        <section className="mt-8 rounded-xl border border-dashed border-bio-border bg-bio-panel p-8 text-center">
          <h2 className="text-xl font-semibold text-bio-text">Waiting for BioVolt telemetry</h2>
          <p className="mt-2 text-bio-muted">Connect a device to view backend-processed measurements.</p>
        </section>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-5xl">
      <h1 className="text-3xl font-semibold tracking-tight text-bio-text">Overview</h1>
      <TelemetryHeader frame={frame} wsState={wsState} />

      <MetricGrid>
        <MetricCard label="BPV Voltage" value={frame.electrical.voltage_mv} digits={1} unit="mV" />
        <MetricCard label="Current" value={frame.electrical.current_ua} digits={2} unit="µA" />
        <MetricCard label="Power" value={frame.electrical.power_uw} digits={2} unit="µW" />
        <MetricCard
          label="Cumulative Energy"
          value={frame.electrical.cumulative_energy_mj}
          digits={2}
          unit="mJ"
        />
        <MetricCard label="OD680" value={frame.biological.od680} digits={2} unit="unitless" />
        <MetricCard label="Temperature" value={frame.environment.temperature_c} digits={1} unit="°C" />
        <MetricCard label="Light" value={frame.environment.lux} digits={0} unit="lux" />
        <MetricCard label="Grow LED PWM" value={frame.actuators.grow_led_pwm} digits={0} unit="raw 0-255" />
        <article className="rounded-xl border border-bio-border bg-bio-panel p-4">
          <p className="text-sm font-medium text-bio-muted">Mixer</p>
          <p className="mt-2 text-2xl font-semibold tracking-tight text-bio-text">
            {frame.actuators.mixer_on ? 'On' : 'Off'}
          </p>
        </article>
        <article className="rounded-xl border border-bio-border bg-bio-panel p-4">
          <p className="text-sm font-medium text-bio-muted">Control Mode</p>
          <p className="mt-2 text-2xl font-semibold tracking-tight text-bio-text">{formatMode(frame.control.mode)}</p>
        </article>
      </MetricGrid>
    </div>
  )
}
