import { useSystemStatus } from '../hooks/useSystemStatus'
import { formatTimestamp } from '../lib/format'

function ageLabel(ageMs: number | null): string {
  if (ageMs === null) return 'No telemetry yet'
  if (ageMs < 1_000) return 'Less than 1 s ago'
  return `${Math.round(ageMs / 1_000)} s ago`
}

export function SystemPage() {
  const { status, loading, error } = useSystemStatus()

  return (
    <div className="mx-auto max-w-5xl">
      <header>
        <p className="page-kicker">Monitor / System</p>
        <h1 className="page-title mt-2">System</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-bio-muted">
          Service health and device freshness from the backend status endpoint.
        </p>
      </header>

      {loading && !status ? <p className="mt-8 text-sm text-bio-muted">Loading system status…</p> : null}
      {error ? <p className="mt-8 rounded-lg border border-bio-danger/40 bg-bio-danger/10 p-4 text-sm text-bio-danger" role="alert">{error}</p> : null}

      {status ? (
        <>
          <section className="mt-8 grid gap-4 sm:grid-cols-3" aria-label="Service health">
            <article className="surface p-4">
              <p className="text-sm text-bio-muted">Backend</p>
              <p className="mt-2 flex items-center gap-2 text-lg font-semibold text-bio-success"><span aria-hidden="true" className="h-2 w-2 rounded-full bg-bio-success" />Operational</p>
            </article>
            <article className="surface p-4">
              <p className="text-sm text-bio-muted">Database</p>
              <p className={`mt-2 flex items-center gap-2 text-lg font-semibold ${status.database === 'ok' ? 'text-bio-success' : 'text-bio-danger'}`}><span aria-hidden="true" className={`h-2 w-2 rounded-full ${status.database === 'ok' ? 'bg-bio-success' : 'bg-bio-danger'}`} />{status.database === 'ok' ? 'Operational' : 'Unavailable'}</p>
            </article>
            <article className="surface p-4">
              <p className="text-sm text-bio-muted">Connected devices</p>
              <p className="data-value mt-2 text-lg font-semibold text-bio-text">{status.device_count}</p>
            </article>
          </section>

          <section className="surface mt-6 overflow-hidden" aria-labelledby="connected-devices-heading">
            <div className="border-b border-bio-border px-5 py-4">
              <h2 id="connected-devices-heading" className="text-base font-semibold text-bio-text">Connected devices</h2>
              <p className="mt-1 text-sm text-bio-muted">Latest telemetry receipt for each registered source.</p>
            </div>
            {status.connected_devices.length === 0 ? (
              <p className="px-5 py-8 text-sm text-bio-muted">No devices are currently connected.</p>
            ) : (
              <ul className="divide-y divide-bio-border/70">
                {status.connected_devices.map((deviceId) => {
                  const device = status.devices[deviceId]
                  return (
                    <li className="flex flex-wrap items-center justify-between gap-3 px-5 py-4" key={deviceId}>
                      <div>
                        <p className="text-sm font-semibold text-bio-text">{deviceId}</p>
                        <p className="mt-1 text-xs text-bio-muted">{device?.latest_telemetry_at ? `Latest frame ${formatTimestamp(device.latest_telemetry_at)}` : 'No frame received'}</p>
                      </div>
                      <span className="rounded-full border border-bio-border px-2.5 py-1 text-xs text-bio-muted">{ageLabel(device?.latest_telemetry_age_ms ?? null)}</span>
                    </li>
                  )
                })}
              </ul>
            )}
          </section>
        </>
      ) : null}
    </div>
  )
}
