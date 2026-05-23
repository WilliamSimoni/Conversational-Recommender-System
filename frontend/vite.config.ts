import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': `http://${process.env.BACKEND_HOST || 'localhost'}:8000`
    },
    watch: {
      usePolling: true,
    }
  }
})
