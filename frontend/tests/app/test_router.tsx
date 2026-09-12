import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { appRoutes } from '../../src/app/router'

function renderAt(path: string) {
  const router = createMemoryRouter(appRoutes, { initialEntries: [path] })
  render(<RouterProvider router={router} />)
  return router
}

describe('application routes', () => {
  it('renders Charts through the shared shell at /charts', () => {
    renderAt('/charts')

    expect(screen.getByRole('banner')).toHaveTextContent('BioVolt')
    expect(screen.getByRole('heading', { name: 'Charts' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Charts' })).toHaveAttribute('aria-current', 'page')
  })

  it.each([
    ['/', 'Overview'],
    ['/live', 'Live Data'],
    ['/charts', 'Charts'],
    ['/system', 'System'],
  ])('renders the %s route with a semantic heading', (path, heading) => {
    renderAt(path)
    expect(screen.getByRole('heading', { name: heading })).toBeInTheDocument()
  })

  it('opens and closes the mobile navigation with a keyboard reachable button', async () => {
    const user = userEvent.setup()
    renderAt('/')

    const menuButton = screen.getByRole('button', { name: 'Toggle navigation menu' })
    expect(menuButton).toHaveAttribute('aria-expanded', 'false')

    await user.click(menuButton)
    expect(menuButton).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByRole('navigation')).toBeVisible()

    await user.keyboard('{Escape}')
    expect(menuButton).toHaveAttribute('aria-expanded', 'false')
  })
})
