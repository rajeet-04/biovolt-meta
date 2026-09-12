import { defineConfig } from 'vitest/config'
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

export default defineConfig({
  plugins: [react(), VitePWA(pwaOptions)],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: './tests/setup.ts',
    include: ['tests/**/test_*.{ts,tsx}'],
    globals: true,
    css: true,
  },
})
