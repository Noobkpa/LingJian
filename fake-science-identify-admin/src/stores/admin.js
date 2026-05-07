import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/utils/request'
import { V1 } from '@/api/v1/endpoints'

export const useAdminStore = defineStore('admin', () => {
  const token = ref(localStorage.getItem('admin_token') || '')
  const adminInfo = ref(JSON.parse(localStorage.getItem('admin_info') || '{}'))

  const isLogin = computed(() => !!token.value)
  const adminId = computed(() => adminInfo.value.admin_id || '')

  const login = async (loginForm) => {
    const pair = await request.post(V1.AUTH_LOGIN, {
      username: loginForm.username,
      password: loginForm.password
    })
    const p = pair.data
    token.value = p.access_token
    localStorage.setItem('admin_token', p.access_token)
    if (p.refresh_token) {
      localStorage.setItem('refresh_token', p.refresh_token)
    }
    const me = await request.get(V1.USERS_ME)
    const u = me.data
    adminInfo.value = {
      admin_id: u.id,
      username: u.username,
      email: u.email || ''
    }
    localStorage.setItem('admin_info', JSON.stringify(adminInfo.value))
    return pair.data
  }

  const logout = () => {
    token.value = ''
    adminInfo.value = {}
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_info')
    localStorage.removeItem('refresh_token')
  }

  return {
    token,
    adminInfo,
    isLogin,
    adminId,
    login,
    logout
  }
})
