import type { TelemetryMetric } from './series'

export const chartMetadata: Record<TelemetryMetric, { label: string; unit: string }> = {
  voltage_mv: { label: 'BPV Voltage', unit: 'mV' }, current_ua: { label: 'Current', unit: 'µA' }, power_uw: { label: 'Power', unit: 'µW' }, cumulative_energy_mj: { label: 'Cumulative Energy', unit: 'mJ' }, od680: { label: 'OD680', unit: 'unitless' }, temperature_c: { label: 'Temperature', unit: '°C' }, lux: { label: 'Light', unit: 'lux' },
}
