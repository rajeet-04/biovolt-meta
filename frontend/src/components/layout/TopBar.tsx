import { Link } from 'react-router-dom'

interface TopBarProps {
  isMenuOpen: boolean
  onMenuToggle: () => void
}

export function TopBar({ isMenuOpen, onMenuToggle }: TopBarProps) {
  return (
    <header className="sticky top-0 z-20 flex min-h-16 items-center justify-between border-b border-bio-border bg-bio-panel px-4 md:px-6">
      <Link className="flex items-center gap-3 text-bio-text" to="/">
        <span aria-hidden="true" className="h-6 w-1 rounded-sm bg-bio-accent" />
        <span className="text-base font-semibold tracking-tight">BioVolt</span>
        <span className="hidden border-l border-bio-border pl-3 text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-bio-muted md:inline">
          Operator console
        </span>
      </Link>
      <div className="flex items-center gap-4">
        <span className="hidden text-xs text-bio-muted sm:inline">Local telemetry workspace</span>
        <button
          aria-controls="primary-navigation"
          aria-expanded={isMenuOpen}
          aria-label="Toggle navigation menu"
          className="rounded-md border border-bio-border px-3 py-2 text-sm font-medium text-bio-text hover:bg-bio-panel-strong md:hidden"
          onClick={onMenuToggle}
          type="button"
        >
          Menu
        </button>
      </div>
    </header>
  )
}
