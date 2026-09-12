import type { ReactNode } from 'react'

interface AppSurfaceProps {
  children: ReactNode
}

export function AppSurface({ children }: AppSurfaceProps) {
  return <main className="min-h-screen bg-bio-bg text-bio-text">{children}</main>
}
