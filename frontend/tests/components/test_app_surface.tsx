import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { AppSurface } from '../../src/components/layout/AppSurface'

describe('AppSurface', () => {
  it('provides a full-height main landmark around the application content', () => {
    render(
      <AppSurface>
        <p>Dashboard content</p>
      </AppSurface>,
    )

    const main = screen.getByRole('main')
    expect(main).toHaveClass('min-h-screen')
    expect(main).toHaveTextContent('Dashboard content')
  })
})
