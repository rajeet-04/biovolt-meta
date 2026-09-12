import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ExperimentStateBadge } from '../components/experiments/ExperimentStateBadge'
import { OperatorLoginDialog } from '../components/operator/OperatorLoginDialog'
import { getExperiment, transitionExperiment } from '../lib/experimentsApi'
import { useOperatorStore } from '../stores/operatorStore'
import { useOnlineStatus } from '../hooks/useOnlineStatus'
import { useTelemetryStore } from '../stores/telemetryStore'
import type { Experiment } from '../types/experiments'

export function ExperimentDetailPage() {
  const { experimentId = '' } = useParams()
  const [experiment, setExperiment] = useState<Experiment | null>(null)
  const [loginOpen, setLoginOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const authenticated = useOperatorStore((state) => state.authenticated)
  const online = useOnlineStatus()
  const wsState = useTelemetryStore((state) => state.wsState)
  const unavailableReason = !online ? 'Browser is offline.' : wsState !== 'connected' ? 'Backend dashboard is disconnected.' : null

  useEffect(() => { void useOperatorStore.getState().load(); void getExperiment(experimentId).then(setExperiment).catch(() => setError('Experiment unavailable')) }, [experimentId])
  if (error) return <p className="text-red-300" role="alert">{error}</p>
  if (!experiment) return <p className="text-bio-muted">Loading experiment…</p>

  const mutate = async (action: 'ready' | 'start' | 'stop' | 'abort') => {
    if (!online || wsState !== 'connected') { setError(unavailableReason); return }
    if (!authenticated) { setLoginOpen(true); return }
    try { setExperiment(await transitionExperiment(experiment.id, action)); setError(null) } catch { setError(`Unable to ${action} experiment`) }
  }

  return (
    <div className="mx-auto grid max-w-4xl gap-6">
      <div className="flex items-center justify-between"><div><Link className="text-sm text-bio-accent" to="/experiments">← Experiments</Link><h1 className="mt-2 text-3xl font-semibold text-bio-text">{experiment.name}</h1></div><ExperimentStateBadge state={experiment.state} /></div>
      <p className="text-bio-muted">{experiment.description ?? 'No description provided.'}</p>
      {experiment.state === 'completed' ? <Link className="text-bio-accent" to={`/experiments/${experiment.id}/results`}>View results</Link> : null}
      <section className="grid gap-3 rounded-lg border border-bio-border bg-bio-panel p-5"><h2 className="text-lg font-semibold text-bio-text">Start intent</h2><p className="text-sm text-bio-muted">Review device freshness, arm mode, and exact setpoints before starting.</p>{experiment.arms.map((arm) => <div className="rounded border border-bio-border p-3 text-sm text-bio-text" key={arm.id ?? `${arm.device_id}-${arm.cell_id}`}><p>{arm.device_id} / {arm.cell_id}</p><p>Mode: {arm.mode} · LED PWM: {arm.initial_led_pwm} · Mixer: {arm.initial_mixer_on ? 'On' : 'Off'}</p><p className="text-bio-muted">Device freshness is confirmed by the live status view.</p></div>)}</section>
      {error ? <p className="text-sm text-red-300" role="alert">{error}</p> : null}
      {unavailableReason ? <p className="text-sm text-bio-muted" role="status">{unavailableReason}</p> : null}
      <div className="flex flex-wrap gap-2">{experiment.state === 'draft' ? <button className="rounded bg-bio-accent px-3 py-2 text-sm font-semibold text-bio-bg" disabled={Boolean(unavailableReason)} onClick={() => void mutate('ready')} type="button">Mark ready</button> : null}{experiment.state === 'ready' ? <button className="rounded bg-bio-accent px-3 py-2 text-sm font-semibold text-bio-bg" disabled={Boolean(unavailableReason)} onClick={() => void mutate('start')} type="button">Start experiment</button> : null}{experiment.state === 'running' ? <button className="rounded border border-bio-border px-3 py-2 text-sm text-bio-text" disabled={Boolean(unavailableReason)} onClick={() => void mutate('stop')} type="button">Stop safely</button> : null}</div>
      <OperatorLoginDialog onClose={() => setLoginOpen(false)} open={loginOpen} />
    </div>
  )
}
