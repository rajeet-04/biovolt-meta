import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ExperimentForm } from '../components/experiments/ExperimentForm'
import { ExperimentStateBadge } from '../components/experiments/ExperimentStateBadge'
import { OperatorLoginDialog } from '../components/operator/OperatorLoginDialog'
import { createExperiment, listExperiments } from '../lib/experimentsApi'
import { useOperatorStore } from '../stores/operatorStore'
import type { Experiment } from '../types/experiments'

export function ExperimentsPage() {
  const [experiments, setExperiments] = useState<Experiment[]>([])
  const [loginOpen, setLoginOpen] = useState(false)
  const authenticated = useOperatorStore((state) => state.authenticated)

  useEffect(() => {
    void useOperatorStore.getState().load()
    void listExperiments().then(setExperiments).catch(() => setExperiments([]))
  }, [])

  return (
    <div className="mx-auto grid max-w-5xl gap-6">
      <div><h1 className="text-3xl font-semibold tracking-tight text-bio-text">Experiments</h1><p className="mt-2 text-bio-muted">Define exact arm intent before sending any device command.</p></div>
      <section className="grid gap-3">
        {experiments.length === 0 ? <p className="text-sm text-bio-muted">No experiments yet.</p> : experiments.map((experiment) => <Link className="flex items-center justify-between rounded-lg border border-bio-border bg-bio-panel p-4" key={experiment.id} to={`/experiments/${experiment.id}`}><span className="text-bio-text">{experiment.name}</span><ExperimentStateBadge state={experiment.state} /></Link>)}
      </section>
      {authenticated ? <ExperimentForm onSubmit={async (input) => { const created = await createExperiment(input); setExperiments((current) => [created, ...current]) }} /> : <button className="w-fit rounded bg-bio-accent px-4 py-2 text-sm font-semibold text-bio-bg" onClick={() => setLoginOpen(true)} type="button">Unlock experiment controls</button>}
      <OperatorLoginDialog onClose={() => setLoginOpen(false)} open={loginOpen} />
    </div>
  )
}
