import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { MetricCard } from '../../src/components/metrics/MetricCard'
import { MetricGrid } from '../../src/components/metrics/MetricGrid'

describe('MetricCard', () => {
  it('keeps the label visible and renders null values as Unavailable', () => {
    render(<MetricCard label="OD680" value={null} digits={2} unit="unitless" />)

    expect(screen.getByText('OD680')).toBeInTheDocument()
    expect(screen.getByText('Unavailable')).toBeInTheDocument()
  })

  it('renders formatted backend values with their explicit units', () => {
    render(
      <MetricGrid>
        <MetricCard label="BPV Voltage" value={438.2} digits={1} unit="mV" />
        <MetricCard label="Power" value={1.92} digits={2} unit="µW" />
      </MetricGrid>,
    )

    expect(screen.getByText('438.2 mV')).toBeInTheDocument()
    expect(screen.getByText('1.92 µW')).toBeInTheDocument()
  })
})
