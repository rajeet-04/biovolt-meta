import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it, vi } from 'vitest'
import { OperatorLoginDialog } from '../../src/components/operator/OperatorLoginDialog'
import { useOperatorStore } from '../../src/stores/operatorStore'

afterEach(() => { vi.restoreAllMocks(); useOperatorStore.setState({ authenticated: false, expiresAt: null, loading: false, error: null }) })

it('clears the PIN after submit and uses the HttpOnly-cookie login API', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ authenticated: true, expires_at: null }), { status: 200 }))
  const user = userEvent.setup()
  render(<OperatorLoginDialog open />)
  await user.type(screen.getByLabelText('PIN'), '2468')
  await user.click(screen.getByRole('button', { name: 'Unlock controls' }))
  await waitFor(() => expect(screen.queryByLabelText('PIN')).not.toBeInTheDocument())
  expect(globalThis.fetch).toHaveBeenCalledWith('/api/operator/login', expect.objectContaining({ credentials: 'include' }))
})
