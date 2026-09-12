import { NavLink } from 'react-router-dom'
import { useSystemStore } from '../../stores/systemStore'

interface SidebarProps {
  isOpen: boolean
  onNavigate: () => void
}

const links = [
  { label: 'Overview', to: '/' },
  { label: 'Live Data', to: '/live' },
  { label: 'Charts', to: '/charts' },
  { label: 'System', to: '/system' },
  { label: 'Experiments', to: '/experiments' },
  { label: 'Control', to: '/control' },
  { label: 'Calibration', to: '/calibration' },
]

export function Sidebar({ isOpen, onNavigate }: SidebarProps) {
  const publicMode = useSystemStore((state) => state.capabilities?.access_mode === 'public_read_only')
  const visibleLinks = publicMode ? links.filter((link) => !['/control', '/calibration'].includes(link.to)) : links
  return (
    <aside
      className={`${isOpen ? 'block' : 'hidden'} border-b border-bio-border bg-bio-panel md:block md:min-h-[calc(100vh-4rem)] md:w-60 md:border-b-0 md:border-r`}
    >
      <nav aria-label="Primary navigation" className="p-4" id="primary-navigation">
        <ul className="m-0 grid list-none gap-1 p-0">
          {visibleLinks.map((link) => (
            <li key={link.to}>
              <NavLink
                className={({ isActive }) =>
                  `block rounded-md px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-bio-accent ${
                    isActive
                      ? 'bg-bio-panel-strong text-bio-accent'
                      : 'text-bio-muted hover:bg-bio-panel-strong hover:text-bio-text'
                  }`
                }
                end={link.to === '/'}
                onClick={onNavigate}
                to={link.to}
              >
                {link.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  )
}
