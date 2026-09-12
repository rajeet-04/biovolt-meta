import { useSystemStore } from '../../stores/systemStore'
export function AccessModeBanner() { const mode = useSystemStore((state) => state.capabilities?.access_mode); return mode === 'public_read_only' ? <div className="border-b border-amber-700 bg-amber-950/40 px-4 py-2 text-center text-sm text-amber-100" role="status">Read-only judge view</div> : null }
