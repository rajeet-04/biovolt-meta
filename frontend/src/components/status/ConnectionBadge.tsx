type ConnectionState = 'connecting' | 'connected' | 'disconnected'

interface ConnectionBadgeProps {
  state: ConnectionState
}

const labels: Record<ConnectionState, string> = {
  connecting: 'Backend reconnecting',
  connected: 'Backend connected',
  disconnected: 'Backend disconnected',
}

const tones: Record<ConnectionState, { dot: string; text: string }> = {
  connecting: { dot: 'bg-bio-warning', text: 'text-bio-warning' },
  connected: { dot: 'bg-bio-success', text: 'text-bio-success' },
  disconnected: { dot: 'bg-bio-danger', text: 'text-bio-danger' },
}

export function ConnectionBadge({ state }: ConnectionBadgeProps) {
  return (
    <span
      aria-live="polite"
      className={`brutal-tag ${tones[state].text}`}
      role="status"
    >
      <span aria-hidden="true" className={`h-2 w-2 ${tones[state].dot}`} />
      {labels[state]}
    </span>
  )
}
