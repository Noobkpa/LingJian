/**
 * API 根路径：默认 `/api/v1`（走 Vite `/api` 代理）。
 * 若代理异常导致 404，可在审核端目录添加 `.env.development`：
 *   VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
 * 保存后重启 `npm run dev`，浏览器将直连后端（需后端已开 CORS）。
 */
const raw = import.meta.env.VITE_API_BASE_URL
export const API_BASE =
  typeof raw === 'string' && raw.trim().length > 0
    ? raw.trim().replace(/\/+$/, '')
    : '/api/v1'
