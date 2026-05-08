/**
 * 灵鉴后端默认前缀 `/api/v1`（axios baseURL 已含此前缀）
 * 路径与 backend/app/api/v1 下各 router 的 prefix + 装饰路径一致。
 */
export const V1 = {
  AUTH_CAPTCHA: '/auth/captcha',
  AUTH_LOGIN: '/auth/login',
  AUTH_REGISTER: '/auth/register',
  AUTH_REFRESH: '/auth/refresh',

  USERS_ME: '/users/me',

  ROLES: '/roles',

  ANALYZE_TEXT: '/analyze/text',
  ANALYZE_IMAGE: '/analyze/image',
  ANALYZE_MIXED: '/analyze/mixed',
  ANALYZE_HISTORY: '/analyze/history',
  ANALYZE_HISTORY_DELETE: '/analyze/history/delete',
  ANALYZE_HISTORY_ALL: '/analyze/history/all',
  ANALYZE_RESULT: (publicId) => `/analyze/results/${encodeURIComponent(publicId)}`,

  FEEDBACK: '/feedback/',

  CONTENTS_TEXT: '/contents/text',
  CONTENTS_IMAGE: '/contents/image',
  CONTENTS_MIXED: '/contents/mixed',
  CONTENTS_BATCH_ZIP: '/contents/batch_zip',

  TASK: (taskId) => `/tasks/${encodeURIComponent(taskId)}`,

  SEARCH: '/search',

  ADMIN_STATS_OVERVIEW: '/admin/stats/overview',
  ADMIN_STATS_RISK_BUCKETS: '/admin/stats/risk_buckets',
  ADMIN_STATS_DAILY: '/admin/stats/daily',

  REVIEW_QUEUE: '/review/queue',
  REVIEW_ACTION: '/review/action',

  EXPORTS: '/exports'
}

export const AUTH_BODY_ONLY_PATHS = [
  V1.AUTH_CAPTCHA,
  V1.AUTH_LOGIN,
  V1.AUTH_REGISTER,
  V1.AUTH_REFRESH
]

export function isAuthBodyOnlyPath(url) {
  if (!url) return false
  return AUTH_BODY_ONLY_PATHS.some((p) => url.includes(p))
}
