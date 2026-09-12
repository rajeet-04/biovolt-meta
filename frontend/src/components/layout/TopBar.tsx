import { Link } from 'react-router-dom'

interface TopBarProps {
  isMenuOpen: boolean
  onMenuToggle: () => void
}

export function TopBar({ isMenuOpen, onMenuToggle }: TopBarProps) {
  return (
    <header className="sticky top-0 z-20 flex min-h-16 items-center justify-between border-b-2 border-bio-border bg-bio-panel px-4 md:px-6">
      <Link className="flex items-center gap-3 text-bio-text" to="/">
        <span aria-hidden="true" className="h-7 w-2 bg-bio-accent" />
        <span className="text-base font-black tracking-tight">BioVolt</span>
        <span className="hidden border-l-2 border-bio-border pl-3 text-[0.68rem] font-black uppercase tracking-[0.14em] text-bio-muted md:inline">
          Signal board
        </span>
      </Link>
      <div className="flex items-center gap-4">
        <span className="hidden text-xs font-semibold uppercase tracking-[0.12em] text-bio-muted sm:inline">Local telemetry workspace</span>
        <button
          aria-controls="primary-navigation"
          aria-expanded={isMenuOpen}
          aria-label="Toggle navigation menu"
          className="border-2 border-bio-border px-3 py-2 text-sm font-bold text-bio-text hover:bg-bio-accent hover:text-white md:hidden"
          onClick={onMenuToggle}
          type="button"
        >
          Menu
        </button>
      </div>
    </header>
  )
}
