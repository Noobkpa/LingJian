import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import router from '@/router'
import { V1, isAuthBodyOnlyPath } from '@/api/v1/endpoints'

// 创建axios实例（与灵鉴后端 LINGJIAN_API_PREFIX 默认 /api/v1 对齐）
// 同步识别含 BERT +（可选）本地 LLM 首次加载，可能远超 2 分钟；超时过短会像「点了没反应」
const request = axios.create({
  baseURL: '/api/v1',
  timeout: 1_800_000 // 30 分钟；仍不够可在 identify 里单独传更大 timeout
})

/** 无拦截器的客户端，用于刷新 token，避免循环依赖 */
const rawClient = axios.create({
  baseURL: '/api/v1',
  timeout: 30000
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    // 登录/注册不要带过期 Bearer，避免干扰；刷新接口也不带（用 body 里的 refresh_token）
    if (userStore.token && !isAuthBodyOnlyPath(config.url || '')) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const res = response.data
    // 旧版统一包裹 { code, data }；FastAPI 直接返回 JSON 无 code 字段
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

      // 401：后端登录失败也是 401（用户名或密码错误），不能与「过期」混为一谈
      if (status === 401) {
        const publicAuth = isAuthBodyOnlyPath(cfg?.url || '')
        if (publicAuth) {
          ElMessage.error(message)
          return Promise.reject(error)
        }

        // access 过期：尝试用 refresh_token 续期一次
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken && cfg && !cfg._retry) {
          try {
            const refreshResp = await rawClient.post(V1.AUTH_REFRESH, {
              refresh_token: refreshToken
            })
            const pair = refreshResp.data
            const access = pair.access_token
            const nextRefresh = pair.refresh_token
            localStorage.setItem('token', access)
            localStorage.setItem('refresh_token', nextRefresh)
            const userStore = useUserStore()
            userStore.token = access

            cfg._retry = true
            cfg.headers = cfg.headers || {}
            cfg.headers.Authorization = `Bearer ${access}`
            return request(cfg)
          } catch {
            // refresh 失败则走下方登出
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
        error.code === 'ECONNABORTED' ||
        msg.toLowerCase().includes('timeout')
      if (aborted) {
        ElMessage.error(
          '请求超时：模型加载或推理耗时较长。若仍失败可稍后重试，或让后端适当增大超时时间。'
        )
      } else {
        ElMessage.error('网络异常，请检查网络连接')
      }
    }
    return Promise.reject(error)
  }
)

export default request