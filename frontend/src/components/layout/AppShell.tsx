import { useEffect, useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'
import { AccessModeBanner } from '../access/AccessModeBanner'
import { useSystemStore } from '../../stores/systemStore'

export function AppShell() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const loadCapabilities = useSystemStore((state) => state.loadCapabilities)

  useEffect(() => { void loadCapabilities() }, [loadCapabilities])

  useEffect(() => {
    const closeMenu = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setIsMenuOpen(false)
    }
    document.addEventListener('keydown', closeMenu)
    return () => document.removeEventListener('keydown', closeMenu)
  }, [])

  return (
    <div className="min-h-screen">
      <TopBar isMenuOpen={isMenuOpen} onMenuToggle={() => setIsMenuOpen((open) => !open)} />
      <AccessModeBanner />
      <div className="md:flex">
        <Sidebar isOpen={isMenuOpen} onNavigate={() => setIsMenuOpen(false)} />
        <section className="min-w-0 flex-1 p-4 md:p-8">
          <Outlet />
        </section>
      </div>
    </div>
  )
}
