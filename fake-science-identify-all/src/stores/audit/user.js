import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/utils/request'
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
  // 状态定义
  const token = ref(localStorage.getItem('audit_token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('audit_user_info') || '{}'))

  // 计算属性
  const isLogin = computed(() => !!token.value)
  const auditorId = computed(() => userInfo.value.auditor_id || '')

  const login = async (loginForm) => {
    const pair = await request.post(V1.AUTH_LOGIN, {
      username: loginForm.username,
      password: loginForm.password,
      captcha_id: loginForm.captcha_id,
      captcha_code: loginForm.captcha_code
    })
    const p = pair.data
    token.value = p.access_token
    localStorage.setItem('audit_token', p.access_token)
    if (p.refresh_token) {
      localStorage.setItem('audit_refresh_token', p.refresh_token)
    }
    const me = await request.get(V1.USERS_ME)
    userInfo.value = mapMeToAuditUser(me.data)
    localStorage.setItem('audit_user_info', JSON.stringify(userInfo.value))
    return pair.data
  }

  // 退出登录
  const logout = () => {
    token.value = ''
    userInfo.value = {}
    localStorage.removeItem('audit_token')
    localStorage.removeItem('audit_user_info')
    localStorage.removeItem('audit_refresh_token')
  }

  return {
    token,
    userInfo,
    isLogin,
    auditorId,
    login,
    logout
  }
})
