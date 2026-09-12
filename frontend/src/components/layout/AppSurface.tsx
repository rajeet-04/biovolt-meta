import type { ReactNode } from 'react'

interface AppSurfaceProps {
  children: ReactNode
}

export function AppSurface({ children }: AppSurfaceProps) {
  return <main className="min-h-screen">{children}</main>
}
