import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'
import { V1 } from '@/api/v1/endpoints'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || '{}'))

  const isLogin = computed(() => !!token.value)
  const userId = computed(() => userInfo.value.user_id || '')

  /** 后端 TokenPair + GET /users/me，与 LoginRequest / RegisterRequest 响应一致 */
  async function applySessionFromTokenPair(wrapped) {
    const p = wrapped.data
    token.value = p.access_token
    localStorage.setItem('token', p.access_token)
    if (p.refresh_token) {
      localStorage.setItem('refresh_token', p.refresh_token)
    }
    const me = await request.get(V1.USERS_ME)
    userInfo.value = {
      user_id: me.data.id,
      username: me.data.username,
      nickname: me.data.username,
      phone: '',
      email: me.data.email || '',
      register_time: ''
    }
    localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
    return p
  }

  const login = async (loginForm) => {
    const pair = await request.post(V1.AUTH_LOGIN, {
      username: loginForm.username,
      password: loginForm.password
    })
    await applySessionFromTokenPair(pair)
    return pair.data
  }

  /** RegisterRequest: username, password, email? — 无邮箱字段时传 null */
  const register = async (registerForm) => {
    const pair = await request.post(V1.AUTH_REGISTER, {
      username: registerForm.username,
      password: registerForm.password,
      email: null
    })
    await applySessionFromTokenPair(pair)
    return pair.data
  }

  const logout = () => {
    token.value = ''
    userInfo.value = {}
    localStorage.clear()
  }

  const updateUserInfo = async (updateForm) => {
    ElMessage.info('当前后端未提供资料修改接口，仅本地展示')
    userInfo.value = {
      ...userInfo.value,
      nickname: updateForm.nickname ?? userInfo.value.nickname,
      phone: updateForm.phone ?? userInfo.value.phone
    }
    localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
    return { userInfo: userInfo.value }
  }

  const updatePassword = async (_passwordForm) => {
    ElMessage.warning('当前后端未开放修改密码接口')
    return {}
  }

  const cancelAccount = async () => {
    ElMessage.warning('当前后端未开放注销接口')
  }

  return {
    token,
    userInfo,
    isLogin,
    userId,
    login,
    register,
    logout,
    updateUserInfo,
    updatePassword,
    cancelAccount
  }
})
