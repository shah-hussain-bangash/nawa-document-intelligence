import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const local = loadEnv(mode, '.', 'NAWA_')
  const target = `http://127.0.0.1:${local.NAWA_API_PORT || '8000'}`
  return {
    plugins: [react()],
    build: {
      rollupOptions: {
        output: {
          manualChunks: { charts: ['recharts'], react: ['react', 'react-dom', 'react-router-dom'] },
        },
      },
    },
    server: {
      host: '127.0.0.1',
      port: Number(local.NAWA_WEB_PORT || '5173'),
      strictPort: true,
      proxy: {
        '/api': target,
        '/auth': target,
        '/health': target,
      },
    },
  }
})
