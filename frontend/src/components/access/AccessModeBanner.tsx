import { useSystemStore } from '../../stores/systemStore'

export function AccessModeBanner() {
  const mode = useSystemStore((state) => state.capabilities?.access_mode)

  return mode === 'public_read_only' ? (
    <div className="flex items-center justify-center gap-2 border-b border-bio-warning/40 bg-bio-warning/10 px-4 py-2 text-center text-sm text-bio-warning" role="status">
      <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-bio-warning" />
      <span>Read-only judge view</span>
    </div>
  ) : null
}
