import { act, render, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { OverviewPage } from '../../src/pages/OverviewPage'
import {
  useDashboardSocket,
  type DashboardSocketClientFactory,
  type DashboardSocketClientLike,
} from '../../src/hooks/useDashboardSocket'
import { useTelemetryStore } from '../../src/stores/telemetryStore'
import type { ProcessedTelemetryV1 } from '../../src/types/telemetry'

function frame(deviceId: string, cellId: string): ProcessedTelemetryV1 {
  return {
    schema_version: 1,
    device_id: deviceId,
    cell_id: cellId,
    sequence: 7,
    timestamp: '2026-08-24T12:00:00Z',
    electrical: {
      voltage_mv: 1000,
      current_ua: 50,
      power_uw: 50,
      load_resistance_ohm: 20_000,
      cumulative_energy_mj: 5.5,
    },
    biological: {
      od680: 0.3,
      biomass_g_l: null,
      biomass_total_g: null,
      biomass_delta_g: null,
      co2_biofixed_g: null,
    },
    environment: { temperature_c: 22, lux: 500 },
    actuators: { grow_led_pwm: 64, mixer_on: false },
    control: { mode: 'monitor' },
  }
}

interface CapturedClient {
  client: DashboardSocketClientLike
  handlers: Parameters<DashboardSocketClientFactory>[0]
}

function makeFactory(
  clients: CapturedClient[],
): (factory: DashboardSocketClientFactory) => DashboardSocketClientFactory {
  return (factory) => (handlers) => {
    const client = factory(handlers)
    clients.push({ client, handlers })
    return client
  }
}

function DashboardHarness({ factory }: { factory: DashboardSocketClientFactory }) {
  useDashboardSocket({ clientFactory: factory })
  return <OverviewPage />
}

const expectedLabels = [
  'BPV Voltage',
  'Current',
  'Power',
  'Cumulative Energy',
  'OD680',
  'Temperature',
  'Light',
  'Grow LED PWM',
  'Mixer',
  'Control Mode',
]

function assertSameMetricStructure(container: HTMLElement) {
  for (const label of expectedLabels) {
    expect(within(container).getByText(label)).toBeInTheDocument()
  }
}

function assertNoSimulatorLabel(container: HTMLElement) {
  expect(within(container).queryByText(/simulator/i)).toBeNull()
}

beforeEach(() => {
  useTelemetryStore.setState({
    sources: {},
    selectedSource: null,
    wsState: 'disconnected',
    lastSocketError: null,
  })
})

afterEach(() => {
  vi.restoreAllMocks()
  vi.useRealTimers()
})

describe('source replacement integration', () => {
  it('renders the same metric structure with a different device id and never shows a Simulator label', () => {
    const firstClients: CapturedClient[] = []
    const firstView = render(
      <DashboardHarness
        factory={makeFactory(firstClients)(
          (handlers) => {
            handlers.onState('connected')
            return { start: vi.fn(), stop: vi.fn() }
          },
        )}
      />,
    )

    act(() => firstClients[0]!.handlers.onTelemetry(frame('biovolt-sim-01', 'cell-a')))

    const firstContainer = firstView.container
    const firstLabels = firstContainer.textContent ?? ''
    expect(within(firstContainer).getByText('biovolt-sim-01 · cell-a')).toBeInTheDocument()
    assertSameMetricStructure(firstContainer)
    assertNoSimulatorLabel(firstContainer)

    firstView.unmount()
    useTelemetryStore.setState({
      sources: {},
      selectedSource: null,
      wsState: 'disconnected',
      lastSocketError: null,
    })

    const secondClients: CapturedClient[] = []
    const secondView = render(
      <DashboardHarness
        factory={makeFactory(secondClients)(
          (handlers) => {
            handlers.onState('connected')
            return { start: vi.fn(), stop: vi.fn() }
          },
        )}
      />,
    )

    act(() => secondClients[0]!.handlers.onTelemetry(frame('biovolt-01', 'cell-a')))

    const secondContainer = secondView.container
    expect(within(secondContainer).getByText('biovolt-01 · cell-a')).toBeInTheDocument()
    expect(within(secondContainer).queryByText('biovolt-sim-01 · cell-a')).toBeNull()
    assertSameMetricStructure(secondContainer)
    assertNoSimulatorLabel(secondContainer)

    const secondLabels = secondContainer.textContent ?? ''
    for (const label of expectedLabels) {
      expect(firstLabels).toContain(label)
      expect(secondLabels).toContain(label)
    }

    secondView.unmount()
  })
})
