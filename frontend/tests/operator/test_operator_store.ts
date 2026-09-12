import { act } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useOperatorStore } from '../../src/stores/operatorStore'

afterEach(() => {
  vi.restoreAllMocks()
  useOperatorStore.setState({ authenticated: false, expiresAt: null, loading: false, error: null })
})

describe('operator store', () => {
  it('loads session state without exposing cookie material', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ authenticated: true, expires_at: '2026-08-27T18:00:00Z' }), { status: 200 }))
    await act(async () => { await useOperatorStore.getState().load() })
    expect(useOperatorStore.getState().authenticated).toBe(true)
    expect(useOperatorStore.getState()).not.toHaveProperty('token')
    expect(globalThis.fetch).toHaveBeenCalledWith('/api/operator/session', expect.objectContaining({ credentials: 'include' }))
  })
})
