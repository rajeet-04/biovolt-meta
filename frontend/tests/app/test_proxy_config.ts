// @vitest-environment node

import { describe, expect, it } from 'vitest'
import { buildProxyConfig } from '../../vite.config'

describe('BioVolt preview proxy configuration', () => {
  it('defaults BIOVOLT_PROXY_TARGET to http://localhost:8000 for both /api and /ws', () => {
    const proxy = buildProxyConfig({})

    expect(proxy['/api']).toEqual({
      target: 'http://localhost:8000',
      changeOrigin: true,
    })
    expect(proxy['/ws']).toEqual({
      target: 'http://localhost:8000',
      ws: true,
      changeOrigin: true,
    })
  })

  it('uses BIOVOLT_PROXY_TARGET override for both /api and /ws and keeps ws: true on /ws', () => {
    const proxy = buildProxyConfig({ BIOVOLT_PROXY_TARGET: 'http://backend:8000' })

    expect(proxy['/api']).toEqual({
      target: 'http://backend:8000',
      changeOrigin: true,
    })
    expect(proxy['/ws']).toEqual({
      target: 'http://backend:8000',
      ws: true,
      changeOrigin: true,
    })
  })
})
