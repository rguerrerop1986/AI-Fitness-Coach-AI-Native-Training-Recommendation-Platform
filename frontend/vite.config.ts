import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5174,
    watch: {
      usePolling: true
    },
    // Proxy /api to backend. Use 127.0.0.1 (same machine as Vite); requests from other devices hit this server, then proxy forwards to backend here.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  define: {
    global: 'globalThis',
  },
  css: {
    postcss: './postcss.config.js',
  },
  build: {
    cssCodeSplit: false,
  }
})
