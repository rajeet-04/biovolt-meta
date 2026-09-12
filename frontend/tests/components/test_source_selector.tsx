import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it } from 'vitest'
import { SourceSelector } from '../../src/components/status/SourceSelector'
import type { ProcessedTelemetryV1 } from '../../src/types/telemetry'
import { useTelemetryStore } from '../../src/stores/telemetryStore'

function frame(deviceId: string, cellId: string, sequence: number): ProcessedTelemetryV1 {
  return {
    schema_version: 1,
    device_id: deviceId,
    cell_id: cellId,
    sequence,
    timestamp: '2026-08-24T12:00:00Z',
    electrical: {
      voltage_mv: 438.2,
      current_ua: 4.382,
      power_uw: 1.92,
      load_resistance_ohm: 100_000,
      cumulative_energy_mj: null,
    },
    biological: {
      od680: null,
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

describe('SourceSelector', () => {
  it('shows one source identity without an unnecessary dropdown', () => {
    useTelemetryStore.getState().ingest(frame('biovolt-01', 'cell-a', 1))

    render(<SourceSelector />)

    expect(screen.getByText('biovolt-01 · cell-a')).toBeInTheDocument()
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
    expect(screen.queryByText('Simulator')).not.toBeInTheDocument()
  })

  it('allows selecting a source when multiple sources are available', async () => {
    useTelemetryStore.getState().ingest(frame('biovolt-01', 'cell-a', 1))
    useTelemetryStore.getState().ingest(frame('hardware-02', 'cell-b', 2))

    render(<SourceSelector />)
    const user = userEvent.setup()
    const selector = screen.getByRole('combobox', { name: 'Telemetry source' })

    expect(screen.getByRole('option', { name: 'biovolt-01 · cell-a' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'hardware-02 · cell-b' })).toBeInTheDocument()

    await user.selectOptions(selector, 'hardware-02::cell-b')

    expect(useTelemetryStore.getState().selectedSource).toBe('hardware-02::cell-b')
    expect(selector).toHaveValue('hardware-02::cell-b')
  })
})
