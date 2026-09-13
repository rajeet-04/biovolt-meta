import type { ExperimentArm } from '../types/experiments'

export interface CommandRecord {
  command_id: string
  device_id: string
  status: 'queued' | 'sent' | 'accepted' | 'applied' | 'rejected' | 'failed' | 'expired'
  kind: string
  reason_code: string | null
  message: string | null
  applied_state: { mode: string; grow_led_pwm: number; mixer_on: boolean } | null
}

async function request(path: string, init?: RequestInit): Promise<CommandRecord> {
  const response = await fetch(path, { ...init, credentials: 'include', headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) } })
  const body: unknown = await response.json().catch(() => null)
  if (!response.ok || !body || typeof body !== 'object') throw new Error(`Control request failed (${response.status})`)
  return body as CommandRecord
}

export async function sendControlCommand(command: Pick<ExperimentArm, 'device_id'> & { kind: string; payload: Record<string, unknown>; ttl_ms?: number }): Promise<CommandRecord> {
  return request('/api/commands', { method: 'POST', body: JSON.stringify(command) })
}

export async function getCommand(commandId: string): Promise<CommandRecord> {
  return request(`/api/commands/${encodeURIComponent(commandId)}`)
}
