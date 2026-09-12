import { Link } from 'react-router-dom'

interface TopBarProps {
  isMenuOpen: boolean
  onMenuToggle: () => void
}

export function TopBar({ isMenuOpen, onMenuToggle }: TopBarProps) {
  return (
    <header className="flex min-h-16 items-center justify-between border-b border-bio-border bg-bio-panel px-4 md:px-6">
      <Link
        className="text-lg font-semibold tracking-tight text-bio-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-bio-accent"
        to="/"
      >
        BioVolt
      </Link>
      <button
        aria-controls="primary-navigation"
        aria-expanded={isMenuOpen}
        aria-label="Toggle navigation menu"
        className="rounded-md border border-bio-border px-3 py-2 text-sm text-bio-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-bio-accent md:hidden"
        onClick={onMenuToggle}
        type="button"
      >
        Menu
      </button>
    </header>
  )
}
