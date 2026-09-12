import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ConnectionBadge } from '../../src/components/status/ConnectionBadge'
import { FreshnessBadge } from '../../src/components/status/FreshnessBadge'
import { isTelemetryStale, telemetryAgeMs } from '../../src/lib/stale'

const timestamp = '2026-08-24T12:00:00.000Z'
const nowMs = Date.parse('2026-08-24T12:00:03.000Z')

describe('telemetry freshness', () => {
  it('calculates the age from the backend timestamp', () => {
    expect(telemetryAgeMs(timestamp, nowMs)).toBe(3_000)
  })

  it('keeps telemetry fresh just below the default threshold', () => {
    expect(isTelemetryStale(timestamp, nowMs - 1)).toBe(false)
  })

  it('marks telemetry stale just above the default threshold', () => {
    expect(isTelemetryStale(timestamp, nowMs + 1)).toBe(true)
  })
})

describe('FreshnessBadge', () => {
  it('shows Live below the stale threshold', () => {
    render(<FreshnessBadge timestamp={timestamp} nowMs={nowMs - 1} />)

    expect(screen.getByRole('status')).toHaveTextContent('Live')
  })

  it('shows Stale above the stale threshold', () => {
    render(<FreshnessBadge timestamp={timestamp} nowMs={nowMs + 1} />)

    expect(screen.getByRole('status')).toHaveTextContent('Stale')
  })
})

describe('ConnectionBadge', () => {
  it.each([
    ['connecting', 'Backend reconnecting'],
    ['connected', 'Backend connected'],
    ['disconnected', 'Backend disconnected'],
  ] as const)('describes %s without relying on color', (state, label) => {
    render(<ConnectionBadge state={state} />)

    expect(screen.getByRole('status')).toHaveTextContent(label)
  })
})
