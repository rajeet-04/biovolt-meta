import { describe, expect, it } from 'vitest'
import { deriveFreshness } from '../../src/lib/dataFreshness'
import { isCacheableRequest } from '../../src/pwa/cachePolicy'

describe('production access and freshness', () => {
  it.each([[2, 'live'], [2.01, 'stale'], [6, 'stale'], [6.01, 'device_disconnected']] as const)('maps age %s to %s', (age, state) => expect(deriveFreshness({ ageSeconds: age, backendReachable: true, dashboardConnected: true, hasData: true })).toBe(state))
  it('distinguishes backend loss from cached offline state', () => { expect(deriveFreshness({ ageSeconds: null, backendReachable: false, dashboardConnected: false, hasData: false })).toBe('backend_disconnected'); expect(deriveFreshness({ ageSeconds: null, backendReachable: false, dashboardConnected: false, hasData: true, cached: true })).toBe('cached_offline') })
  it('never caches mutation methods or control paths', () => { expect(isCacheableRequest(new Request('https://biovolt.test/api/experiments', { method: 'POST' }))).toBe(false); expect(isCacheableRequest(new Request('https://biovolt.test/api/control'))).toBe(false); expect(isCacheableRequest(new Request('https://biovolt.test/assets/app.js'))).toBe(true) })
})
