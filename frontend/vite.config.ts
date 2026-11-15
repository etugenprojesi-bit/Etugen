import react from '@vitejs/plugin-react'
import { readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { dirname, join } from 'node:path'
import { defineConfig, type Plugin } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// MapLibre 6 loads its web worker from a file next to its own module, which
// is lost when Vite bundles it. Serve/emit the (self-contained) worker at a
// fixed path instead; MapView calls setWorkerUrl(MAPLIBRE_WORKER_PATH).
// Backend for the /api proxy; override with API_URL when port 8000 is taken.
const API_URL = process.env.API_URL ?? 'http://localhost:8000'

const MAPLIBRE_WORKER_PATH = '/maplibre/maplibre-gl-worker.mjs'
const maplibreDist = dirname(createRequire(import.meta.url).resolve('maplibre-gl/package.json')) + '/dist'

function maplibreWorker(): Plugin {
  const source = () => readFileSync(join(maplibreDist, 'maplibre-gl-worker.mjs'))
  return {
    name: 'maplibre-worker',
    configureServer(server) {
      server.middlewares.use(MAPLIBRE_WORKER_PATH, (_req, res) => {
        res.setHeader('Content-Type', 'text/javascript')
        res.end(source())
      })
    },
    generateBundle() {
      this.emitFile({ type: 'asset', fileName: MAPLIBRE_WORKER_PATH.slice(1), source: source() })
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  define: { __MAPLIBRE_WORKER_PATH__: JSON.stringify(MAPLIBRE_WORKER_PATH) },
  plugins: [
    react(),
    maplibreWorker(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'Etügen',
        short_name: 'Etügen',
        description: 'NASA verileriyle ürün rotasyonu karar desteği',
        lang: 'tr',
        theme_color: '#2f6b3a',
        background_color: '#f6f4ee',
        display: 'standalone',
        start_url: '/',
        icons: [
          { src: 'icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: 'icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,mjs,css,html,svg,png}'],
        maximumFileSizeToCacheInBytes: 4 * 1024 * 1024,
        navigateFallbackDenylist: [/^\/api\//],
        runtimeCaching: [
          {
            // Analysis results are public data: keep the last ones for offline use.
            urlPattern: ({ url }) => url.pathname === '/api/analyze',
            handler: 'NetworkFirst',
            options: {
              cacheName: 'analysis',
              networkTimeoutSeconds: 20,
              expiration: { maxEntries: 20, maxAgeSeconds: 7 * 24 * 3600 },
            },
          },
          {
            // Risk layers and satellite series: public data too; a new point can take
            // up to a few minutes on Earth Engine, so wait longer before using the cache.
            urlPattern: ({ url }) => url.pathname === '/api/risk' || url.pathname === '/api/satellite',
            handler: 'NetworkFirst',
            options: {
              cacheName: 'layers',
              networkTimeoutSeconds: 60,
              expiration: { maxEntries: 20, maxAgeSeconds: 7 * 24 * 3600 },
            },
          },
        ],
      },
    }),
  ],
  server: {
    host: true, // reachable from a phone on the same Wi-Fi
    proxy: { '/api': API_URL },
  },
  preview: {
    host: true,
    proxy: { '/api': API_URL },
  },
})
