import { SourceSelector } from '../components/status/SourceSelector'
import { TelemetryFieldTable } from '../components/metrics/TelemetryFieldTable'
import { formatNullableNumber, formatTimestamp, formatMode } from '../lib/format'
import { useTelemetryStore } from '../stores/telemetryStore'

export function LiveDataPage() {
  const sources = useTelemetryStore((state) => state.sources)
  const selected = useTelemetryStore((state) => state.selectedSource)
  const frame = selected ? sources[selected]?.latest : undefined

  if (!frame) return <div className="mx-auto max-w-5xl"><h1 className="text-3xl font-semibold text-bio-text">Live Data</h1><p className="mt-3 text-bio-muted">Waiting for BioVolt telemetry</p></div>

  const n = (value: number | null, digits = 2) => formatNullableNumber(value, digits)
  const groups = [
    { name: 'Electrical', fields: [{ label: 'Voltage', value: n(frame.electrical.voltage_mv), unit: 'mV' }, { label: 'Current', value: n(frame.electrical.current_ua), unit: 'µA' }, { label: 'Power', value: n(frame.electrical.power_uw), unit: 'µW' }, { label: 'Cumulative Energy', value: n(frame.electrical.cumulative_energy_mj), unit: 'mJ' }] },
    { name: 'Biological', fields: [{ label: 'OD680', value: n(frame.biological.od680) }, { label: 'Biomass', value: n(frame.biological.biomass_g_l), unit: 'g/L' }, { label: 'Estimated CO2 biofixed into biomass', value: n(frame.biological.co2_biofixed_g), unit: 'g' }] },
    { name: 'Environment', fields: [{ label: 'Temperature', value: n(frame.environment.temperature_c), unit: '°C' }, { label: 'Light', value: n(frame.environment.lux), unit: 'lux' }] },
    { name: 'Actuators', fields: [{ label: 'Grow LED PWM', value: frame.actuators.grow_led_pwm, unit: 'raw 0-255' }, { label: 'Mixer', value: frame.actuators.mixer_on ? 'On' : 'Off' }] },
    { name: 'Control', fields: [{ label: 'Control Mode', value: formatMode(frame.control.mode) }] },
    { name: 'Identity/Freshness', fields: [{ label: 'Device', value: frame.device_id }, { label: 'Cell', value: frame.cell_id }, { label: 'Sequence', value: frame.sequence }, { label: 'Timestamp', value: <time dateTime={frame.timestamp} title={frame.timestamp}>{formatTimestamp(frame.timestamp)}</time> }] },
  ]
  return (
    <div className="mx-auto max-w-5xl">
      <div className="flex flex-wrap items-center justify-between gap-3"><h1 className="text-3xl font-semibold tracking-tight text-bio-text">Live Data</h1><SourceSelector /></div>
      <p className="mt-3 mb-6 text-bio-muted">Latest processed telemetry from the backend.</p>
      <TelemetryFieldTable groups={groups} />
    </div>
  )
}
