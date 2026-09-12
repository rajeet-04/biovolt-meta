export type FreshnessState = 'loading' | 'live' | 'stale' | 'device_disconnected' | 'backend_disconnected' | 'cached_offline' | 'no_data' | 'error'
export function deriveFreshness({ ageSeconds, backendReachable, dashboardConnected, hasData, cached }: { ageSeconds: number | null; backendReachable: boolean; dashboardConnected: boolean; hasData: boolean; cached?: boolean }): FreshnessState {
  if (!backendReachable && !dashboardConnected) return cached ? 'cached_offline' : 'backend_disconnected'
  if (!hasData || ageSeconds == null) return backendReachable ? 'no_data' : 'backend_disconnected'
  if (ageSeconds <= 2) return dashboardConnected && backendReachable ? 'live' : 'device_disconnected'
  if (ageSeconds <= 6) return 'stale'
  return 'device_disconnected'
}
