import { useEffect, useState } from 'react'
import { useOperatorStore } from '../../stores/operatorStore'

interface OperatorLoginDialogProps {
  open: boolean
  onClose?: () => void
}

export function OperatorLoginDialog({ open, onClose }: OperatorLoginDialogProps) {
  const [pin, setPin] = useState('')
  const authenticated = useOperatorStore((state) => state.authenticated)
  const error = useOperatorStore((state) => state.error)
  const loading = useOperatorStore((state) => state.loading)
  const login = (value: string) => useOperatorStore.getState().login(value)

  useEffect(() => {
    if (authenticated) {
      onClose?.()
    }
  }, [authenticated, onClose])

  if (!open || authenticated) return null

  return (
    <div aria-modal="true" className="fixed inset-0 z-50 grid place-items-center bg-black/60 p-4" role="dialog">
      <form
        className="w-full max-w-sm rounded-lg border border-bio-border bg-bio-panel p-6 shadow-xl"
        onSubmit={(event) => {
          event.preventDefault()
          const submittedPin = pin
          setPin('')
          void login(submittedPin)
        }}
      >
        <h2 className="text-xl font-semibold text-bio-text">Operator access</h2>
        <p className="mt-2 text-sm text-bio-muted">Authenticate to change experiment or actuator state.</p>
        <label className="mt-5 block text-sm text-bio-text" htmlFor="operator-pin">
          PIN
        </label>
        <input
          autoComplete="off"
          className="mt-1 w-full rounded-md border border-bio-border bg-bio-panel-strong px-3 py-2 text-bio-text"
          id="operator-pin"
          inputMode="numeric"
          onChange={(event) => setPin(event.target.value)}
          type="password"
          value={pin}
        />
        {error ? <p className="mt-2 text-sm text-red-300" role="alert">{error}</p> : null}
        <button className="mt-5 rounded-md bg-bio-accent px-4 py-2 text-sm font-semibold text-bio-bg" disabled={loading || pin.length === 0} type="submit">
          {loading ? 'Checking…' : 'Unlock controls'}
        </button>
      </form>
    </div>
  )
}
