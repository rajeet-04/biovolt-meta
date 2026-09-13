import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'
import { ControlPage } from '../../src/pages/ControlPage'
import { useOperatorStore } from '../../src/stores/operatorStore'
import { useTelemetryStore } from '../../src/stores/telemetryStore'

beforeEach(() => {
  useOperatorStore.setState({ authenticated: true, expiresAt: null, loading: false, error: null })
  useTelemetryStore.setState({ sources: {}, selectedSource: null, wsState: 'disconnected', lastSocketError: null })
})

describe('ControlPage safety states', () => {
  it('disables all actuator controls while backend is disconnected', () => {
    render(<ControlPage />)
    expect(screen.getByText('Backend dashboard is disconnected.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Safe Stop' })).toBeDisabled()
  })
})
