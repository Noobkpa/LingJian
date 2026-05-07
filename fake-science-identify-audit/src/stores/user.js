import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import request, { rawClient } from '@/utils/request'
import { V1 } from '@/api/v1/endpoints'

function mapMeToAuditUser(u) {
  let joinTime = ''
  if (u.created_at) {
    const s = String(u.created_at)
    joinTime = s.includes('T') ? s.replace('T', ' ').slice(0, 19) : s
  }
  return {
    auditor_id: u.id,
    username: u.username,
    email: u.email || '',
    nickname: u.nickname || '',
    phone: u.phone || '',
    join_time: joinTime,
    roles: [],
    role_label: '用户',
    audit_count: 0,
    accuracy_display: '100%'
  }
}

export const useUserStore = defineStore('auditUser', () => {
  const token = ref(localStorage.getItem('audit_token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('audit_user_info') || '{}'))

  const isLogin = computed(() => !!token.value)
  const auditorId = computed(() => userInfo.value.auditor_id || '')

  /**
   * 优先拉取审核端扩展资料；若后端无 /users/me/profile（旧版本）则回退到 /users/me，避免登录后整页报 Not Found。
   */
  const fetchProfile = async () => {
    if (!token.value) return
    const headers = { Authorization: `Bearer ${token.value}` }

    const prof = await rawClient.get(V1.USERS_PROFILE, {
      headers,
      validateStatus: (s) => s === 200 || s === 404
    })

    if (prof.status === 200) {
      const p = prof.data
      userInfo.value = {
        auditor_id: p.id,
        username: p.username,
        email: p.email || '',
        nickname: p.nickname || '',
        phone: p.phone || '',
        join_time: p.join_time || '',
        roles: p.roles || [],
        role_label: p.role_label || '',
        audit_count: p.audit_count ?? 0,
        accuracy_display: p.accuracy_display ?? '100%'
      }
      localStorage.setItem('audit_user_info', JSON.stringify(userInfo.value))
      return
    }

    const me = await rawClient.get(V1.USERS_ME, {
      headers,
      validateStatus: (s) => s === 200 || s === 401 || s === 403 || s === 404
    })

    if (me.status === 200) {
      userInfo.value = mapMeToAuditUser(me.data)
      localStorage.setItem('audit_user_info', JSON.stringify(userInfo.value))
      return
    }

    const detail =
      typeof me.data?.detail === 'string' ? me.data.detail : '加载用户信息失败'
    ElMessage.error(detail)
  }

  const login = async (loginForm) => {
    const pair = await request.post(V1.AUTH_LOGIN, {
      username: loginForm.username,
      password: loginForm.password
    })

    const p = pair.data

    token.value = p.access_token
    localStorage.setItem('audit_token', p.access_token)

    if (p.refresh_token) {
      localStorage.setItem('audit_refresh_token', p.refresh_token)
    }

    await fetchProfile()

    return pair.data
  }

  const logout = () => {
    token.value = ''
    userInfo.value = {}
    localStorage.removeItem('audit_token')
    localStorage.removeItem('audit_user_info')
    localStorage.removeItem('audit_refresh_token')
  }

  const updatePassword = async ({ old_password, new_password }) => {
    await request.post(V1.USERS_PASSWORD, {
      old_password,
      new_password
    })
  }

  return {
    token,
    userInfo,
    isLogin,
    auditorId,
    login,
    logout,
    fetchProfile,
    updatePassword
  }
})
