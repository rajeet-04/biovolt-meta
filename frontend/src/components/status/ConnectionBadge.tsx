type ConnectionState = 'connecting' | 'connected' | 'disconnected'

interface ConnectionBadgeProps {
  state: ConnectionState
}

const labels: Record<ConnectionState, string> = {
  connecting: 'Backend reconnecting',
  connected: 'Backend connected',
  disconnected: 'Backend disconnected',
}

export function ConnectionBadge({ state }: ConnectionBadgeProps) {
  return (
    <span
      aria-live="polite"
      className="inline-flex items-center rounded-full border border-bio-border px-2.5 py-1 text-xs font-medium text-bio-text"
      role="status"
    >
      {labels[state]}
    </span>
  )
}
