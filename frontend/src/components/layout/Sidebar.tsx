import { NavLink } from 'react-router-dom'

interface SidebarProps {
  isOpen: boolean
  onNavigate: () => void
}

const links = [
  { label: 'Overview', to: '/' },
  { label: 'Live Data', to: '/live' },
  { label: 'Charts', to: '/charts' },
  { label: 'System', to: '/system' },
]

export function Sidebar({ isOpen, onNavigate }: SidebarProps) {
  return (
    <aside
      className={`${isOpen ? 'block' : 'hidden'} border-b border-bio-border bg-bio-panel md:block md:min-h-[calc(100vh-4rem)] md:w-60 md:border-b-0 md:border-r`}
    >
      <nav aria-label="Primary navigation" className="p-4" id="primary-navigation">
        <ul className="m-0 grid list-none gap-1 p-0">
          {links.map((link) => (
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
