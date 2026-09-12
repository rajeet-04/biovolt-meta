import { act, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { App } from '../../src/app/App'

afterEach(() => {
  vi.restoreAllMocks()
})

describe('App', () => {
  it('renders the BioVolt application title', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          backend: 'ok',
          database: 'ok',
          connected_devices: [],
          device_count: 0,
          devices: {},
        }),
        { status: 200, headers: { 'content-type': 'application/json' } },
      ),
    )
    await act(async () => {
      render(<App />)
      await Promise.resolve()
    })
    expect(screen.getByText('BioVolt')).toBeInTheDocument()
  })
})
