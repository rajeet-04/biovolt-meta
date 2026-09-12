import type { Capabilities } from '../types/capabilities'

export async function fetchCapabilities(): Promise<Capabilities> {
  const response = await fetch('/api/capabilities', { credentials: 'include' })
  if (!response.ok) throw new Error('Capabilities unavailable')
  const value: unknown = await response.json()
  if (!value || typeof value !== 'object' || !('access_mode' in value) || (value.access_mode !== 'operator' && value.access_mode !== 'public_read_only')) throw new Error('Invalid capabilities')
  return value as Capabilities
}
