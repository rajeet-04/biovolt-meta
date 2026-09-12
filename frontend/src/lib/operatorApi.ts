import type { OperatorSession } from '../types/operator'

async function request(path: string, init?: RequestInit): Promise<unknown> {
  const response = await fetch(path, {
    ...init,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
  })
  let body: unknown = null
  try {
    body = await response.json()
  } catch {
    // Keep the error generic; response bodies are not trusted UI content.
  }
  if (!response.ok) throw new Error(`Operator request failed (${response.status})`)
  return body
}

function parseSession(value: unknown): OperatorSession {
  if (!value || typeof value !== 'object') throw new Error('Invalid operator session response')
  const record = value as Record<string, unknown>
  if (typeof record.authenticated !== 'boolean') throw new Error('Invalid operator session response')
  const rawExpiry = record.expires_at
  if (rawExpiry !== null && typeof rawExpiry !== 'string') {
    throw new Error('Invalid operator session response')
  }
  return { authenticated: record.authenticated, expiresAt: rawExpiry }
}

export async function getOperatorSession(): Promise<OperatorSession> {
  return parseSession(await request('/api/operator/session'))
}

export async function loginOperator(pin: string): Promise<OperatorSession> {
  return parseSession(await request('/api/operator/login', { method: 'POST', body: JSON.stringify({ pin }) }))
}

export async function logoutOperator(): Promise<OperatorSession> {
  return parseSession(await request('/api/operator/logout', { method: 'POST' }))
}
