import { render, screen } from '@testing-library/react'
import { beforeEach, expect, it } from 'vitest'
import { LiveDataPage } from '../../src/pages/LiveDataPage'
import { useTelemetryStore } from '../../src/stores/telemetryStore'

const frame = { schema_version: 1 as const, device_id: 'biovolt-01', cell_id: 'cell-a', sequence: 7, timestamp: '2026-08-24T10:00:00Z', electrical: { voltage_mv: 438.2, current_ua: 10.5, power_uw: 4.6, load_resistance_ohm: 100, cumulative_energy_mj: null }, biological: { od680: 0.42, biomass_g_l: null, biomass_total_g: null, biomass_delta_g: null, co2_biofixed_g: null }, environment: { temperature_c: 24, lux: 100 }, actuators: { grow_led_pwm: 128, mixer_on: true }, control: { mode: 'monitor' as const } }

beforeEach(() => useTelemetryStore.setState({ sources: {}, selectedSource: null }))

it('renders waiting state without telemetry', () => { render(<LiveDataPage />); expect(screen.getByText('Waiting for BioVolt telemetry')).toBeInTheDocument() })
it('renders exact processed fields and unavailable nulls', () => { useTelemetryStore.getState().ingest(frame); render(<LiveDataPage />); expect(screen.getByText('438.20 mV')).toBeInTheDocument(); expect(screen.getByText('Unavailable mJ')).toBeInTheDocument(); expect(screen.getByText('7')).toBeInTheDocument(); expect(screen.getByText('Estimated CO2 biofixed into biomass')).toBeInTheDocument() })
