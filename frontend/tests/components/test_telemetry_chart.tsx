import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { chartMetadata } from '../../src/components/charts/chartMetadata'
import { TelemetryChart } from '../../src/components/charts/TelemetryChart'
import type { ChartPoint } from '../../src/components/charts/series'

describe('chartMetadata', () => {
  it.each([
    ['voltage_mv', 'BPV Voltage', 'mV'],
    ['current_ua', 'Current', 'µA'],
    ['power_uw', 'Power', 'µW'],
    ['cumulative_energy_mj', 'Cumulative Energy', 'mJ'],
    ['od680', 'OD680', 'unitless'],
    ['temperature_c', 'Temperature', '°C'],
    ['lux', 'Light', 'lux'],
  ] as const)('provides the %s display label and unit', (metric, label, unit) => {
    expect(chartMetadata[metric]).toEqual({ label, unit })
  })
})

describe('TelemetryChart', () => {
  it('renders the supplied empty message without an invented chart line', () => {
    const { container } = render(
      <TelemetryChart title="Power" unit="µW" points={[]} emptyMessage="No power telemetry yet" />,
    )

    expect(screen.getByRole('heading', { name: 'Power' })).toBeInTheDocument()
    expect(screen.getByText('No power telemetry yet')).toBeInTheDocument()
    expect(container.querySelector('[data-chart-line]')).not.toBeInTheDocument()
  })

  it('shows the unit and preserves null measurements as chart gaps', () => {
    const points: ChartPoint[] = [
      { timestampMs: Date.parse('2026-08-24T12:00:00Z'), value: 1.92 },
      { timestampMs: Date.parse('2026-08-24T12:00:01Z'), value: null },
    ]

    const { container } = render(
      <TelemetryChart title="Power" unit="µW" points={points} emptyMessage="No power telemetry yet" />,
    )

    expect(screen.getByText('Unit: µW')).toBeInTheDocument()
    expect(screen.getByText('Null measurements are shown as gaps.')).toBeInTheDocument()
    expect(container.querySelector('[data-chart-line="preserves-null-gaps"]')).toBeInTheDocument()
  })

  it('summarizes the supplied sample count and time range', () => {
    const points: ChartPoint[] = [
      { timestampMs: Date.parse('2026-08-24T12:00:00Z'), value: 1 },
      { timestampMs: Date.parse('2026-08-24T12:00:05Z'), value: 2 },
    ]

    render(<TelemetryChart title="Power" unit="µW" points={points} emptyMessage="No power telemetry yet" />)

    expect(screen.getByText(/Showing 2 samples from/)).toBeInTheDocument()
  })
})
