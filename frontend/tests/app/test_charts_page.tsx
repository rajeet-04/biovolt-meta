import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ChartsPage } from '../../src/pages/ChartsPage'
import * as api from '../../src/lib/api'
import { useTelemetryStore } from '../../src/stores/telemetryStore'
import type { ProcessedTelemetryV1 } from '../../src/types/telemetry'

const mockedHistory = vi.spyOn(api, 'getTelemetryHistory')
const latestTimestamp = Date.parse('2026-08-24T12:10:00.000Z')

function frame(timestampMs: number, overrides: Partial<ProcessedTelemetryV1> = {}): ProcessedTelemetryV1 {
  return {
    schema_version: 1,
    device_id: 'biovolt-01',
    cell_id: 'cell-a',
    sequence: 12,
    timestamp: new Date(timestampMs).toISOString(),
    electrical: {
      voltage_mv: 438.2,
      current_ua: 4.382,
      power_uw: 1.92,
      load_resistance_ohm: 100_000,
      cumulative_energy_mj: 12.34,
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
    ...overrides,
  }
}

beforeEach(() => {
  useTelemetryStore.setState({
    sources: {},
    selectedSource: null,
    wsState: 'disconnected',
    lastSocketError: null,
  })
  mockedHistory.mockReturnValue({ data: [], loading: false, error: null, reload: vi.fn() })
})

describe('ChartsPage', () => {
  it('shows source-neutral mode selection and filters Live 60 s by timestamp without changing the buffer', async () => {
    const old = frame(latestTimestamp - 60_001, { sequence: 1 })
    const boundary = frame(latestTimestamp - 60_000, { sequence: 2 })
    const latest = frame(latestTimestamp, { sequence: 3 })
    useTelemetryStore.getState().ingest(old)
    useTelemetryStore.getState().ingest(boundary)
    useTelemetryStore.getState().ingest(latest)

    render(<ChartsPage />)

    expect(screen.getByText('biovolt-01 · cell-a')).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: 'Chart data mode' })).toHaveValue('live-60s')
    const power = screen.getByRole('region', { name: 'Power' })
    expect(within(power).getByText(/Showing 2 samples from/)).toBeInTheDocument()
    expect(useTelemetryStore.getState().sources['biovolt-01::cell-a']!.liveBuffer).toHaveLength(3)

    const user = userEvent.setup()
    await user.selectOptions(screen.getByRole('combobox', { name: 'Chart data mode' }), 'live-10m')

    expect(within(screen.getByRole('region', { name: 'Power' })).getByText(/Showing 3 samples from/)).toBeInTheDocument()
  })

  it('renders all required charts and an explicit unavailable state for an all-null metric', () => {
    useTelemetryStore.getState().ingest(
      frame(latestTimestamp, {
        biological: {
          od680: null,
          biomass_g_l: null,
          biomass_total_g: null,
          biomass_delta_g: null,
          co2_biofixed_g: null,
        },
      }),
    )

    render(<ChartsPage />)

    for (const title of ['Power', 'BPV Voltage', 'Current', 'OD680', 'Temperature', 'Light', 'Cumulative Energy']) {
      expect(screen.getByRole('heading', { name: title })).toBeInTheDocument()
    }
    expect(screen.getByText('No valid OD680 data available.')).toBeInTheDocument()
  })

  it('loads recent stored samples for the selected source without changing the live socket mode', async () => {
    const stored = frame(latestTimestamp - 120_000, { sequence: 22, electrical: { ...frame(latestTimestamp).electrical, power_uw: 2.5 } })
    mockedHistory.mockImplementation((deviceId: string | null, cellId: string | null) => ({
      data: deviceId === null || cellId === null ? [] : [stored],
      loading: false,
      error: null,
      reload: vi.fn(),
    }))
    useTelemetryStore.getState().ingest(frame(latestTimestamp))

    render(<ChartsPage />)

    const user = userEvent.setup()
    await user.selectOptions(screen.getByRole('combobox', { name: 'Chart data mode' }), 'history')

    expect(screen.getByText('Data mode: Recent stored samples')).toBeInTheDocument()
    expect(screen.getByText('biovolt-01 · cell-a')).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: 'Chart data mode' })).toHaveValue('history')
  })
})
