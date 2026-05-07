import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/utils/request'

export const useUserStore = defineStore('auditUser', () => {
  // 状态定义
  const token = ref(localStorage.getItem('audit_token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('audit_user_info') || '{}'))

  // 计算属性
  const isLogin = computed(() => !!token.value)
  const auditorId = computed(() => userInfo.value.auditor_id || '')

  // 【真实后端】登录方法
  const login = async (loginForm) => {
    const { data } = await request.post('/auditor/login', loginForm)
    token.value = data.token
    userInfo.value = data.userInfo
    localStorage.setItem('audit_token', data.token)
    localStorage.setItem('audit_user_info', JSON.stringify(data.userInfo))
    return data
  }

  // 退出登录
  const logout = () => {
    token.value = ''
    userInfo.value = {}
    localStorage.clear()
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