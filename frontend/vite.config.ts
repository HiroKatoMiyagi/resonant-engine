import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // ⚠️ WebSocketプロキシ設定（Sprint 15）
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
