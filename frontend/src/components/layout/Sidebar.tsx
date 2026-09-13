import { NavLink } from 'react-router-dom'
import { useSystemStore } from '../../stores/systemStore'

interface SidebarProps {
  isOpen: boolean
  onNavigate: () => void
}

const sections = [
  {
    label: 'Monitor',
    links: [
      { label: 'Overview', to: '/' },
      { label: 'Live Data', to: '/live' },
      { label: 'Charts', to: '/charts' },
      { label: 'System', to: '/system' },
    ],
  },
  {
    label: 'Operate',
    links: [
      { label: 'Experiments', to: '/experiments' },
      { label: 'Control', to: '/control' },
      { label: 'Calibration', to: '/calibration' },
    ],
  },
]

export function Sidebar({ isOpen, onNavigate }: SidebarProps) {
  const publicMode = useSystemStore((state) => state.capabilities?.access_mode === 'public_read_only')
  const visibleSections = sections
    .map((section) => ({ ...section, links: publicMode ? section.links.filter((link) => !['/control', '/calibration'].includes(link.to)) : section.links }))
    .filter((section) => section.links.length > 0)
  return (
    <aside
      className={`${isOpen ? 'block' : 'hidden'} border-b border-bio-border bg-bio-panel md:sticky md:top-16 md:block md:h-[calc(100vh-4rem)] md:min-h-[calc(100vh-4rem)] md:w-60 md:flex-none md:border-b-0 md:border-r`}
    >
      <nav aria-label="Primary navigation" className="flex h-full flex-col p-4" id="primary-navigation">
        <div className="grid gap-7">
          {visibleSections.map((section) => (
            <section key={section.label} aria-labelledby={`nav-${section.label.toLowerCase()}`}>
              <h2 id={`nav-${section.label.toLowerCase()}`} className="px-3 text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-bio-muted">
                {section.label}
              </h2>
              <ul className="mt-2 grid list-none gap-1 p-0">
                {section.links.map((link) => (
                  <li key={link.to}>
                    <NavLink
                      className={({ isActive }) =>
                        `flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors ${
                          isActive
                            ? 'bg-bio-panel-strong text-bio-text ring-1 ring-inset ring-bio-border'
                            : 'text-bio-muted hover:bg-bio-panel-strong hover:text-bio-text'
                        }`
                      }
                      end={link.to === '/'}
                      onClick={onNavigate}
                      to={link.to}
                    >
                      {({ isActive }) => (
                        <>
                          <span aria-hidden="true" className={`h-1.5 w-1.5 rounded-full ${isActive ? 'bg-bio-accent' : 'bg-bio-border'}`} />
                          {link.label}
                        </>
                      )}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
        <div className="mt-auto border-t border-bio-border px-3 pt-4">
          <p className="text-xs font-medium text-bio-text">Source-neutral telemetry</p>
          <p className="mt-1 text-xs leading-5 text-bio-muted">Simulator and physical devices use the same dashboard contract.</p>
        </div>
      </nav>
    </aside>
  )
}
