import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // In production, static assets are served by Django at /assets/
  base: '/assets/',
  build: {
    // Build output goes to frontend/dist/ which Django serves
    outDir: 'dist',
    assetsDir: '.',
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
