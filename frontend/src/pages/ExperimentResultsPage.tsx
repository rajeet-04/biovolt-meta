import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ComparisonSummary } from '../components/analytics/ComparisonSummary'
import { ExportExperimentButton } from '../components/analytics/ExportExperimentButton'
import { getAnalyticsSummary } from '../lib/analyticsApi'
import { DataQualityPanel } from '../components/analytics/DataQualityPanel'
import { SeriesSection } from '../components/analytics/SeriesSection'
import type { AnalyticsSummary } from '../types/analytics'
export function ExperimentResultsPage() { const { experimentId = '' } = useParams(); const [summary, setSummary] = useState<AnalyticsSummary | null>(null); const [error, setError] = useState<string | null>(null); useEffect(() => { void getAnalyticsSummary(experimentId).then(setSummary).catch(() => setError('Results are unavailable until analytics data is persisted.')) }, [experimentId]); if (error) return <section className="grid gap-4"><Link className="text-bio-accent" to={`/experiments/${experimentId}`}>← Experiment</Link><p className="text-bio-muted" role="status">{error}</p></section>; if (!summary) return <p className="text-bio-muted">Loading results…</p>; return <section className="mx-auto grid max-w-6xl gap-5"><header><Link className="text-bio-accent" to={`/experiments/${experimentId}`}>← Experiment</Link><h1 className="mt-2 text-3xl font-semibold text-bio-text">Experiment results</h1><p className="text-sm text-bio-muted">Evidence class: {summary.evidence_class}; comparison uses {summary.comparison_method}.</p></header><ComparisonSummary comparison={null} evidenceClass={summary.evidence_class} /><SeriesSection points={[]} /><DataQualityPanel summary={summary} /><ExportExperimentButton experimentId={experimentId} /></section> }
