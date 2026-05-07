import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  // 这里是@别名的核心配置，必须正确
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    // 与 user/admin/audit 错开；作为大系统统一入口「灵鉴门户」
    port: 3080,
    // 开发启动时只自动打开统一入口；子端见 user/admin/audit 的 open:false
    open: true,
    proxy: {
      // 后端挂载在 /api/v1，勿剥离 /api 前缀
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})