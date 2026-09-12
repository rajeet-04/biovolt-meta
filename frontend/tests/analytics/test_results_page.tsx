import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ComparisonSummary } from '../../src/components/analytics/ComparisonSummary'
import { ScientificOutcomes } from '../../src/components/analytics/ScientificOutcomes'

describe('analytics reporting', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('renders unavailable comparison values and human-readable reasons', () => {
    render(<ComparisonSummary comparison={{ eligible: false, passive_energy_mj: null, adaptive_energy_mj: null, gain_pct: null, common_duration_s: null, reasons: ['insufficient_passive_coverage'] }} evidenceClass="measured" />)
    expect(screen.getAllByText('Unavailable').length).toBeGreaterThan(0)
    expect(screen.getByText(/Passive power coverage is below/)).toBeInTheDocument()
  })

  it('keeps synthetic and carbon wording explicit', () => {
    render(<><ComparisonSummary comparison={null} evidenceClass="synthetic_demo" /><ScientificOutcomes outcomes={null} /></>)
    expect(screen.getByText(/Synthetic demo data/)).toBeInTheDocument()
    expect(screen.getByText('Estimated CO2 biofixed into biomass')).toBeInTheDocument()
    expect(screen.queryByText(/statistically significant/i)).not.toBeInTheDocument()
  })
})
