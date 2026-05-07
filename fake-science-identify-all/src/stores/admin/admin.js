import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/utils/request'

export const useAdminStore = defineStore('admin', () => {
  // 状态定义
  const token = ref(localStorage.getItem('admin_token') || '')
  const adminInfo = ref(JSON.parse(localStorage.getItem('admin_info') || '{}'))

  // 计算属性
  const isLogin = computed(() => !!token.value)
  const adminId = computed(() => adminInfo.value.admin_id || '')

  // 登录方法
  const login = async (loginForm) => {
    const { data } = await request.post('/admin/login', loginForm)
    token.value = data.token
    adminInfo.value = data.adminInfo
    localStorage.setItem('admin_token', data.token)
    localStorage.setItem('admin_info', JSON.stringify(data.adminInfo))
    return data
  }

  // 退出登录
  const logout = () => {
    token.value = ''
    adminInfo.value = {}
    localStorage.clear()
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