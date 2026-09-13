import type { ReactNode } from 'react'
import { useSystemStore } from '../../stores/systemStore'
export function CapabilityGate({ capability, children }: { capability: 'can_control' | 'can_manage_experiments' | 'can_manage_calibration'; children: ReactNode }) { const allowed = useSystemStore((state) => state.capabilities?.[capability] ?? true); return allowed ? <>{children}</> : <p className="rounded border border-bio-border p-4 text-sm text-bio-muted" role="status">This action is unavailable in the read-only judge view.</p> }
