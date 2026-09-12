import type { Experiment, ExperimentInput } from '../types/experiments'

async function request(path: string, init?: RequestInit): Promise<unknown> {
  const response = await fetch(path, {
    ...init,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
  })
  const body: unknown = await response.json().catch(() => null)
  if (!response.ok) throw new Error(`Experiment request failed (${response.status})`)
  return body
}

function isExperiment(value: unknown): value is Experiment {
  return Boolean(value && typeof value === 'object' && typeof (value as Experiment).id === 'string')
}

function parseExperiment(value: unknown): Experiment {
  if (!isExperiment(value)) throw new Error('Invalid experiment response')
  return value
}

export async function listExperiments(): Promise<Experiment[]> {
  const value = await request('/api/experiments')
  if (!Array.isArray(value) || !value.every(isExperiment)) throw new Error('Invalid experiment response')
  return value
}

export async function getExperiment(id: string): Promise<Experiment> {
  return parseExperiment(await request(`/api/experiments/${encodeURIComponent(id)}`))
}

export async function createExperiment(input: ExperimentInput): Promise<Experiment> {
  return parseExperiment(await request('/api/experiments', { method: 'POST', body: JSON.stringify(input) }))
}

export async function updateExperiment(id: string, input: Partial<ExperimentInput>): Promise<Experiment> {
  return parseExperiment(await request(`/api/experiments/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify(input) }))
}

export async function transitionExperiment(id: string, action: 'ready' | 'start' | 'stop' | 'abort'): Promise<Experiment> {
  return parseExperiment(await request(`/api/experiments/${encodeURIComponent(id)}/${action}`, { method: 'POST' }))
}
