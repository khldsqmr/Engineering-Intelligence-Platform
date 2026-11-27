//During local development, I use Vite's reverse proxy to forward frontend API requests to FastAPI. This avoids cross-origin complications and allows the frontend to use relative API paths. For production, an equivalent reverse proxy or same-origin deployment would handle this routing.

import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// EIP frontend configuration
export default defineConfig({
  plugins: [react()],

  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,

    proxy: {
      '/api/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },

      '/api/v1': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})

