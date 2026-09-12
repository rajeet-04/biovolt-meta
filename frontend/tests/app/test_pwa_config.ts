// @vitest-environment node

import { describe, expect, it } from 'vitest'
import { pwaManifest, pwaOptions } from '../../vite.config'

describe('BioVolt PWA configuration', () => {
  it('defines an installable dark standalone manifest', () => {
    expect(pwaManifest).toMatchObject({
      name: 'BioVolt',
      short_name: 'BioVolt',
      start_url: '/',
      display: 'standalone',
      theme_color: '#0c100e',
      background_color: '#0c100e',
    })
    expect(pwaManifest.icons).toEqual([
      { src: '/icons/pwa-192x192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
      { src: '/icons/pwa-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
      {
        src: '/icons/pwa-maskable-512x512.png',
        sizes: '512x512',
        type: 'image/png',
        purpose: 'maskable',
      },
    ])
  })

  it('uses an auto-updating shell without caching API responses', () => {
    expect(pwaOptions.registerType).toBe('autoUpdate')
    expect(pwaOptions.workbox?.runtimeCaching).toEqual([])
    expect(pwaOptions.workbox?.navigateFallbackDenylist).toEqual([/^\/api\//])
  })
})
