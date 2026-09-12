import type { ExperimentState } from '../../types/experiments'

export function ExperimentStateBadge({ state }: { state: ExperimentState }) {
  return <span className="rounded-full border border-bio-border px-2 py-1 text-xs text-bio-text">{state}</span>
}
