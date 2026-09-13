import { useSystemStore } from '../../stores/systemStore'

export function AccessModeBanner() {
  const mode = useSystemStore((state) => state.capabilities?.access_mode)

  return mode === 'public_read_only' ? (
    <div className="flex items-center justify-center gap-2 border-b-2 border-bio-warning bg-bio-warning/10 px-4 py-2 text-center text-sm font-semibold text-bio-warning" role="status">
      <span aria-hidden="true" className="h-2 w-2 bg-bio-warning" />
      <span>Read-only judge view · actuation is gated</span>
    </div>
  ) : null
}
