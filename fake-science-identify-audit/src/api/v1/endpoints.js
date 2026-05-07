/**
 * 灵鉴后端前缀 `/api/v1`（axios baseURL 已含此前缀）
 */
export const V1 = {
  AUTH_LOGIN: '/auth/login',
  AUTH_REGISTER: '/auth/register',
  AUTH_REFRESH: '/auth/refresh',

  USERS_ME: '/users/me',
  USERS_PROFILE: '/users/me/profile',
  USERS_PASSWORD: '/users/me/password',

  REVIEW_QUEUE: '/review/queue',
  REVIEW_HISTORY: '/review/history',
  /** 与 REVIEW_HISTORY 同数据；主路径 404 时由前端重试 */
  USERS_ME_REVIEW_HISTORY: '/users/me/review-history',
  REVIEW_ITEM: (publicId) => `/review/item/${encodeURIComponent(publicId)}`,
  REVIEW_ACTION: '/review/action',

  ANALYZE_RESULT: (publicId) => `/analyze/results/${encodeURIComponent(publicId)}`,

  ADMIN_STATS_OVERVIEW: '/admin/stats/overview',
  ADMIN_STATS_RISK_BUCKETS: '/admin/stats/risk_buckets',

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
