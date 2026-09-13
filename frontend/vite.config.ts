import { defineConfig } from 'vitest/config'
import { loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA, type ManifestOptions, type VitePWAOptions } from 'vite-plugin-pwa'

export const pwaManifest = {
  name: 'BioVolt',
  short_name: 'BioVolt',
  description: 'BioVolt biophotovoltaic telemetry dashboard',
  start_url: '/',
  display: 'standalone',
  theme_color: '#0c100e',
  background_color: '#0c100e',
  icons: [
    { src: '/icons/pwa-192x192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
    { src: '/icons/pwa-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
    {
      src: '/icons/pwa-maskable-512x512.png',
      sizes: '512x512',
      type: 'image/png',
      purpose: 'maskable',
    },
  ],
} satisfies Partial<ManifestOptions>

export const pwaOptions = {
  registerType: 'autoUpdate',
  manifest: pwaManifest,
  workbox: {
    globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
    navigateFallbackDenylist: [/^\/api\//],
    runtimeCaching: [],
  },
} satisfies Partial<VitePWAOptions>

export function buildProxyConfig(env: Record<string, string> = {}) {
  const proxyTarget = env.BIOVOLT_PROXY_TARGET || 'http://localhost:8000'
  return {
    '/api': { target: proxyTarget, changeOrigin: true },
    '/ws': { target: proxyTarget, ws: true, changeOrigin: true },
  }
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const proxy = buildProxyConfig(env)

  return {
    plugins: [react(), VitePWA(pwaOptions)],
    server: { proxy },
    preview: { proxy },
    test: {
      environment: 'jsdom',
      setupFiles: './tests/setup.ts',
      include: ['tests/**/test_*.{ts,tsx}'],
      globals: true,
      css: true,
    },
  }
})
