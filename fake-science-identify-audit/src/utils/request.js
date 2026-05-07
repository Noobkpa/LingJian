import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import router from '@/router'
import { V1, isAuthBodyOnlyPath } from '@/api/v1/endpoints'
import { API_BASE } from '@/utils/apiBase'

const request = axios.create({
  baseURL: API_BASE,
  timeout: 1_800_000
})

const rawClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000
})

request.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token && !isAuthBodyOnlyPath(config.url || '')) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

request.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res && typeof res.code === 'number') {
      if (res.code !== 200) {
        ElMessage.error(res.message || '请求失败')
        return Promise.reject(new Error(res.message || '请求失败'))
      }
      return res
    }
    return { code: 200, data: res }
  },
  async (error) => {
    const { response } = error
    const cfg = error.config
    if (response) {
      const status = response.status
      const detail = response.data?.detail
      let detailMsg = ''
      if (typeof detail === 'string') detailMsg = detail
      else if (Array.isArray(detail) && detail[0]?.msg) detailMsg = detail[0].msg
      const message = detailMsg || response.data?.message || '服务器异常'

      if (status === 401) {
        if (isAuthBodyOnlyPath(cfg?.url || '')) {
          ElMessage.error(message)
          return Promise.reject(error)
        }
        const refreshToken = localStorage.getItem('audit_refresh_token')
        if (refreshToken && cfg && !cfg._retry) {
          try {
            const refreshResp = await rawClient.post(V1.AUTH_REFRESH, {
              refresh_token: refreshToken
            })
            const pair = refreshResp.data
            const access = pair.access_token
            const nextRefresh = pair.refresh_token
            localStorage.setItem('audit_token', access)
            if (nextRefresh) localStorage.setItem('audit_refresh_token', nextRefresh)
            const userStore = useUserStore()
            userStore.token = access

            cfg._retry = true
            cfg.headers = cfg.headers || {}
            cfg.headers.Authorization = `Bearer ${access}`
            return request(cfg)
          } catch {
            // fall through
          }
        }
        ElMessage.error('登录已过期或令牌无效，请重新登录')
        const userStore = useUserStore()
        userStore.logout()
        router.replace('/login')
      } else {
        ElMessage.error(message)
      }
    } else {
      const msg = error.message || ''
      const aborted =
        error.code === 'ECONNABORTED' || msg.toLowerCase().includes('timeout')
      if (aborted) {
        ElMessage.error('请求超时，请稍后重试。')
      } else {
        ElMessage.error('网络异常，请检查网络连接')
      }
    }
    return Promise.reject(error)
  }
)

export default request
export { rawClient }
