import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'
import { OverviewPage } from '../../src/pages/OverviewPage'
import { useTelemetryStore } from '../../src/stores/telemetryStore'
import type { ProcessedTelemetryV1 } from '../../src/types/telemetry'

function frame(cumulativeEnergy: number | null = 12.34): ProcessedTelemetryV1 {
  return {
    schema_version: 1,
    device_id: 'biovolt-01',
    cell_id: 'cell-a',
    sequence: 12,
    timestamp: '2026-08-24T12:00:00Z',
    electrical: {
      voltage_mv: 438.2,
      current_ua: 4.382,
      power_uw: 1.92,
      load_resistance_ohm: 100_000,
      cumulative_energy_mj: cumulativeEnergy,
    },
    biological: {
      od680: 0.12,
      biomass_g_l: null,
      biomass_total_g: null,
      biomass_delta_g: null,
      co2_biofixed_g: null,
    },
    environment: { temperature_c: 26.4, lux: 910 },
    actuators: { grow_led_pwm: 130, mixer_on: false },
    control: { mode: 'monitor' },
  }
}

beforeEach(() => {
  useTelemetryStore.setState({
    sources: {},
    selectedSource: null,
    wsState: 'disconnected',
    lastSocketError: null,
  })
})

describe('OverviewPage', () => {
  it('shows a waiting state and backend status when no telemetry is available', () => {
    render(<OverviewPage />)

    expect(screen.getByText('Waiting for BioVolt telemetry')).toBeInTheDocument()
    expect(screen.getByText('Backend disconnected')).toBeInTheDocument()
    expect(screen.queryByText('0 mV')).not.toBeInTheDocument()
  })

  it('renders exact backend values for the selected source', () => {
    useTelemetryStore.getState().ingest(frame())

    render(<OverviewPage />)

    expect(screen.getByText('biovolt-01 · cell-a')).toBeInTheDocument()
    expect(screen.getByText('438.2 mV')).toBeInTheDocument()
    expect(screen.getByText('4.38 µA')).toBeInTheDocument()
    expect(screen.getByText('1.92 µW')).toBeInTheDocument()
    expect(screen.getByText('12.34 mJ')).toBeInTheDocument()
    expect(screen.getByText('0.12 unitless')).toBeInTheDocument()
    expect(screen.getByText('26.4 °C')).toBeInTheDocument()
    expect(screen.getByText('910 lux')).toBeInTheDocument()
  })

  it('renders unavailable energy instead of zero when the backend sends null', () => {
    useTelemetryStore.getState().ingest(frame(null))

    render(<OverviewPage />)

    const energy = screen.getByText('Cumulative Energy').parentElement
    expect(energy).toHaveTextContent('Unavailable')
    expect(energy).not.toHaveTextContent('0 mJ')
  })

  it('shows actuator and control state without rendering controls', () => {
    useTelemetryStore.getState().ingest(frame())

    render(<OverviewPage />)

    expect(screen.getByText('Grow LED PWM')).toBeInTheDocument()
    expect(screen.getByText('130 raw 0-255')).toBeInTheDocument()
    expect(screen.getByText('Mixer')).toBeInTheDocument()
    expect(screen.getByText('Off')).toBeInTheDocument()
    expect(screen.getByText('Control Mode')).toBeInTheDocument()
    expect(screen.getByText('Monitor')).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})
