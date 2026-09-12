import type { CommandRecord } from '../../lib/controlApi'

export function CommandStatus({ command }: { command: CommandRecord | null }) {
  if (!command) return null
  const terminal = ['applied', 'rejected', 'failed', 'expired'].includes(command.status)
  return <p aria-live="polite" className="text-sm text-bio-muted" role="status">Command {command.status}{terminal && command.reason_code ? ` · ${command.reason_code}` : ''}</p>
}
