import { TelemetryHeader } from '../components/status/TelemetryHeader'
import { formatMode, formatNullableNumber } from '../lib/format'
import { useTelemetryStore, type TelemetrySourceState } from '../stores/telemetryStore'
import type { ProcessedTelemetryV1 } from '../types/telemetry'

function latestFrame(sources: Record<string, TelemetrySourceState>, selectedSource: string | null): ProcessedTelemetryV1 | null {
  if (selectedSource && sources[selectedSource]) {
    return sources[selectedSource].latest
  }

  return Object.values(sources)[0]?.latest ?? null
}

function Measurement({ label, value, digits, unit, accent = false }: { label: string; value: number | null; digits: number; unit: string; accent?: boolean }) {
  const formatted = formatNullableNumber(value, digits)
  return (
    <div className="min-w-0 py-4 sm:px-5 sm:py-5">
      <dt className="text-sm text-bio-muted">{label}</dt>
      <dd className={`data-value mt-1 text-xl font-semibold ${accent ? 'text-bio-accent' : 'text-bio-text'}`}>
        {formatted === 'Unavailable' ? formatted : `${formatted} ${unit}`}
      </dd>
    </div>
  )
}

function OverviewIntro() {
  return (
    <header className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
      <div>
        <p className="page-kicker">Monitor / Overview</p>
        <h1 className="page-title mt-2">Overview</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-bio-muted">
          A live view of backend-processed telemetry, device state, and source freshness.
        </p>
      </div>
      <div className="flex items-center gap-3 self-start rounded-lg border border-bio-border bg-bio-panel px-3 py-2.5 lg:self-end">
        <span aria-hidden="true" className="h-2 w-2 rounded-full bg-bio-success" />
        <div>
          <p className="text-xs font-semibold text-bio-text">Operator view</p>
          <p className="text-xs text-bio-muted">Source-neutral telemetry</p>
        </div>
      </div>
    </header>
  )
}

export function OverviewPage() {
  const sources = useTelemetryStore((state) => state.sources)
  const selectedSource = useTelemetryStore((state) => state.selectedSource)
  const wsState = useTelemetryStore((state) => state.wsState)
  const frame = latestFrame(sources, selectedSource)

  if (!frame) {
    return (
      <div className="overview-page mx-auto max-w-[1280px]">
        <OverviewIntro />
        <TelemetryHeader frame={null} wsState={wsState} />
        <section className="surface mt-8 border-dashed bg-bio-panel/70 p-8 text-center md:p-12">
          <div className="mx-auto flex max-w-lg flex-col items-center">
            <span aria-hidden="true" className="h-2 w-2 rounded-full bg-bio-warning" />
            <p className="mt-4 text-xs font-semibold uppercase tracking-[0.14em] text-bio-muted">Awaiting stream</p>
            <h2 className="mt-2 text-xl font-semibold text-bio-text">Waiting for BioVolt telemetry</h2>
            <p className="mt-2 text-sm leading-6 text-bio-muted">Connect a device to view backend-processed measurements.</p>
          </div>
        </section>
      </div>
    )
  }

  return (
    <div className="overview-page mx-auto max-w-[1280px]">
      <OverviewIntro />
      <TelemetryHeader frame={frame} wsState={wsState} />

      <section className="mt-8 grid items-start gap-5 xl:grid-cols-[minmax(0,1.55fr)_minmax(300px,0.75fr)]">
        <article className="surface overflow-hidden">
          <div className="flex flex-wrap items-start justify-between gap-3 border-b border-bio-border px-5 py-4">
            <div>
              <h2 className="text-base font-semibold text-bio-text">Electrical output</h2>
              <p className="mt-1 text-sm text-bio-muted">Backend-derived measurements from the latest frame.</p>
            </div>
            <span className="rounded-full border border-bio-border px-2.5 py-1 text-xs text-bio-muted">Frame {frame.sequence}</span>
          </div>
          <dl className="grid divide-y divide-bio-border/70 px-5 sm:grid-cols-2 sm:divide-x sm:divide-y-0 sm:px-0 xl:grid-cols-4">
            <Measurement label="BPV Voltage" value={frame.electrical.voltage_mv} digits={1} unit="mV" />
            <Measurement label="Current" value={frame.electrical.current_ua} digits={2} unit="µA" />
            <Measurement label="Power" value={frame.electrical.power_uw} digits={2} unit="µW" accent />
            <Measurement label="Cumulative Energy" value={frame.electrical.cumulative_energy_mj} digits={2} unit="mJ" />
          </dl>
        </article>

        <article className="surface p-5">
          <div>
            <h2 className="text-base font-semibold text-bio-text">Operating state</h2>
            <p className="mt-1 text-sm text-bio-muted">Actuation and control state carried by the frame.</p>
          </div>
          <dl className="mt-5 divide-y divide-bio-border/70 border-y border-bio-border/70">
            <div className="flex items-baseline justify-between gap-4 py-3">
              <dt className="text-sm text-bio-muted">Grow LED PWM</dt>
              <dd className="data-value text-sm font-semibold text-bio-text">{frame.actuators.grow_led_pwm} raw 0-255</dd>
            </div>
            <div className="flex items-baseline justify-between gap-4 py-3">
              <dt className="text-sm text-bio-muted">Mixer</dt>
              <dd className="text-sm font-semibold text-bio-text">{frame.actuators.mixer_on ? 'On' : 'Off'}</dd>
            </div>
            <div className="flex items-baseline justify-between gap-4 py-3">
              <dt className="text-sm text-bio-muted">Control Mode</dt>
              <dd className="text-sm font-semibold text-bio-text">{formatMode(frame.control.mode)}</dd>
            </div>
          </dl>
          <div className="mt-5 border-t border-bio-border/70 pt-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="text-sm font-medium text-bio-text">OD680</p>
                <p className="mt-1 text-xs text-bio-muted">Optical reading</p>
              </div>
              <span className="rounded-full border border-bio-warning/40 bg-bio-warning/10 px-2 py-1 text-[0.68rem] font-semibold text-bio-warning">Calibration gated</span>
            </div>
            <p className="data-value mt-2 text-lg font-semibold text-bio-text">
              {formatNullableNumber(frame.biological.od680, 2) === 'Unavailable' ? 'Unavailable' : `${formatNullableNumber(frame.biological.od680, 2)} unitless`}
            </p>
            <p className="mt-1 text-xs leading-5 text-bio-muted">OD680 is available only when valid optical references are present.</p>
          </div>
        </article>
      </section>

      <section className="mt-6">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-bio-text">Environment</h2>
            <p className="mt-1 text-sm text-bio-muted">Ambient context carried alongside the electrical frame.</p>
          </div>
        </div>
        <dl className="surface mt-3 grid divide-y divide-bio-border/70 px-5 sm:grid-cols-2 sm:divide-x sm:divide-y-0 sm:px-0">
          <Measurement label="Temperature" value={frame.environment.temperature_c} digits={1} unit="°C" />
          <Measurement label="Light" value={frame.environment.lux} digits={0} unit="lux" />
        </dl>
      </section>

      <p className="mt-5 text-xs leading-5 text-bio-muted">Values shown are from the latest processed frame. Device identity and freshness remain visible above so synthetic and physical sources are not conflated.</p>
    </div>
  )
}
