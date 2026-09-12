import type { EvidenceClass } from '../../types/analytics'
export function EvidenceBadge({ evidenceClass }: { evidenceClass: EvidenceClass }) { return <span className="inline-flex rounded-full border border-bio-border px-2 py-1 text-xs font-semibold text-bio-text">{evidenceClass === 'synthetic_demo' ? 'Simulation / demo data' : 'Measured evidence'}</span> }
