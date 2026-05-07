/**
 * 灵鉴后端前缀 `/api/v1`（axios baseURL 已含此前缀）
 * 与用户端 fake-science-identify-user 对齐。
 */
export const V1 = {
  AUTH_LOGIN: '/auth/login',
  AUTH_REGISTER: '/auth/register',
  AUTH_REFRESH: '/auth/refresh',

  USERS_ME: '/users/me',

  ANALYZE_TEXT: '/analyze/text',
  ANALYZE_IMAGE: '/analyze/image',
  ANALYZE_MIXED: '/analyze/mixed',
  ANALYZE_HISTORY: '/analyze/history',
  ANALYZE_HISTORY_ALL: '/analyze/history/all',
  ANALYZE_RESULT: (publicId) => `/analyze/results/${encodeURIComponent(publicId)}`,

  ADMIN_STATS_OVERVIEW: '/admin/stats/overview',
  ADMIN_STATS_RISK_BUCKETS: '/admin/stats/risk_buckets',
  ADMIN_STATS_DAILY: '/admin/stats/daily',
  ADMIN_STATS_MODEL_RUNTIME: '/admin/stats/model-runtime',

  REVIEW_QUEUE: '/review/queue',
  REVIEW_ITEM: (publicId) => `/review/item/${encodeURIComponent(publicId)}`,
  REVIEW_ACTION: '/review/action',

  SEARCH: '/search',
  EXPORTS: '/exports'
}

export const AUTH_BODY_ONLY_PATHS = [
  V1.AUTH_LOGIN,
  V1.AUTH_REGISTER,
  V1.AUTH_REFRESH
]

export function isAuthBodyOnlyPath(url) {
  if (!url) return false
  return AUTH_BODY_ONLY_PATHS.some((p) => url.includes(p))
}
