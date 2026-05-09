import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  base: process.env.VITE_PUBLIC_BASE || '/',
  // 这里是@别名的核心配置，必须正确
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 3000,
    // 由门户 3080 进入；避免 start-dev 一次弹出多个浏览器标签
    open: false,
    proxy: {
      // 后端 FastAPI 挂载在 /api/v1，此处不要把 /api 剥掉
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
