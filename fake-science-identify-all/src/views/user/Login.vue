<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1 class="logo">灵鉴</h1>
        <p class="logo-desc">伪科普内容识别系统</p>
      </div>
      <el-tabs v-model="activeTab" type="card" class="login-tabs">
        <!-- 登录面板 -->
        <el-tab-pane label="账号登录" name="login">
          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            size="large"
            label-width="0"
            class="login-form"
          >
            <el-form-item prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="请输入账号"
                :prefix-icon="User"
                clearable
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                :prefix-icon="Lock"
                show-password
                clearable
                @keyup.enter="handleLogin"
              />
            </el-form-item>
            <el-form-item prop="captcha_code">
              <div class="captcha-row">
                <el-input
                  v-model="loginForm.captcha_code"
                  placeholder="图片验证码"
                  clearable
                  @keyup.enter="handleLogin"
                />
                <button type="button" class="captcha-box" title="点击刷新验证码" @click="refreshCaptcha">
                  <img v-if="captcha.image" :src="captcha.image" alt="验证码" />
                  <span v-else>刷新</span>
                  <el-icon><RefreshRight /></el-icon>
                </button>
              </div>
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="loading"
                @click="handleLogin"
                style="width: 100%"
              >
                登录
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 注册面板 -->
        <el-tab-pane label="账号注册" name="register">
          <el-form
            ref="registerFormRef"
            :model="registerForm"
            :rules="registerRules"
            size="large"
            label-width="0"
            class="register-form"
          >
            <el-form-item prop="username">
              <el-input
                v-model="registerForm.username"
                placeholder="请设置登录账号"
                :prefix-icon="User"
                clearable
              />
            </el-form-item>
            <el-form-item prop="nickname">
              <el-input
                v-model="registerForm.nickname"
                placeholder="请设置昵称"
                :prefix-icon="UserFilled"
                clearable
              />
            </el-form-item>
            <el-form-item prop="phone">
              <el-input
                v-model="registerForm.phone"
                placeholder="请输入手机号"
                :prefix-icon="Phone"
                clearable
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="请设置密码"
                :prefix-icon="Lock"
                show-password
                clearable
              />
            </el-form-item>
            <el-form-item prop="confirmPassword">
              <el-input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="请再次确认密码"
                :prefix-icon="Lock"
                show-password
                clearable
                @keyup.enter="handleRegister"
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="loading"
                @click="handleRegister"
                style="width: 100%"
              >
                注册
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user/user'
import { ElMessage } from 'element-plus'
import { User, Lock, UserFilled, Phone, RefreshRight } from '@element-plus/icons-vue'
import { phoneRule, passwordRule } from '@/utils/validate'
import request from '@/utils/request'
import { V1 } from '@/api/v1/endpoints'

const router = useRouter()
const userStore = useUserStore()

// 状态定义
const activeTab = ref('login')
const loading = ref(false)
// 登录表单
const loginFormRef = ref()
const loginForm = reactive({
  username: '',
  password: '',
  captcha_id: '',
  captcha_code: ''
})
const captcha = reactive({
  question: '',
  image: ''
})
const loginRules = {
  username: [
    { required: true, message: '请输入账号', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能少于8位', trigger: 'blur' }
  ],
  captcha_code: [{ required: true, message: '请输入验证码', trigger: 'blur' }]
}

const refreshCaptcha = async () => {
  const { data } = await request.get(V1.AUTH_CAPTCHA)
  loginForm.captcha_id = data.captcha_id
  loginForm.captcha_code = ''
  captcha.question = data.question
  captcha.image = data.image
}
// 注册表单
const registerFormRef = ref()
const registerForm = reactive({
  username: '',
  nickname: '',
  phone: '',
  password: '',
  confirmPassword: ''
})
// 确认密码校验
const validateConfirmPassword = (rule, value, callback) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}
const registerRules = {
  username: [
    { required: true, message: '请设置登录账号', trigger: 'blur' },
    { min: 4, max: 20, message: '账号长度为4-20位', trigger: 'blur' }
  ],
  nickname: [
    { required: true, message: '请设置昵称', trigger: 'blur' }
  ],
  phone: [
    { validator: phoneRule, trigger: 'blur' }
  ],
  password: [
    { validator: passwordRule, trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 登录方法
const handleLogin = async () => {
  if (!loginFormRef.value) return
  const valid = await loginFormRef.value.validate()
  if (!valid) return

  try {
    loading.value = true
    if (!loginForm.captcha_id) await refreshCaptcha()
    await userStore.login(loginForm)
    ElMessage.success('登录成功')
    router.push('/user/home')
  } catch (error) {
    console.error('登录失败', error)
    await refreshCaptcha()
  } finally {
    loading.value = false
  }
}

// 注册方法
const handleRegister = async () => {
  if (!registerFormRef.value) return
  const valid = await registerFormRef.value.validate()
  if (!valid) return

  try {
    loading.value = true
    await userStore.register(registerForm)
    ElMessage.success('注册成功，请登录')
    activeTab.value = 'login'
    // 清空注册表单
    registerFormRef.value.resetFields()
  } catch (error) {
    console.error('注册失败', error)
  } finally {
    loading.value = false
  }
}

onMounted(refreshCaptcha)
</script>

<style scoped>
.login-container {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #4080FF 0%, #66a3ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-box {
  width: 420px;
  background: #fff;
  border-radius: 12px;
  padding: 40px 32px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}
.login-header {
  text-align: center;
  margin-bottom: 24px;
}
.logo {
  font-size: 36px;
  font-weight: bold;
  color: #4080FF;
  margin: 0;
}
.logo-desc {
  font-size: 14px;
  color: #909399;
  margin: 8px 0 0 0;
}
.login-tabs {
  margin-bottom: 16px;
}
.login-form,
.register-form {
  padding-top: 16px;
}
.captcha-row {
  width: 100%;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 150px;
  gap: 10px;
}
.captcha-box {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 0;
  height: 40px;
  border: 1px solid #cfe0ff;
  border-radius: 6px;
  color: #4080ff;
  background: #f2f6ff;
  font-weight: 700;
  cursor: pointer;
}
.captcha-box img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}
.captcha-box :deep(.el-icon) {
  position: absolute;
  right: 6px;
  bottom: 5px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  color: #4080ff;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.12);
}
@media (max-width: 460px) {
  .captcha-row {
    grid-template-columns: 1fr;
  }
}
</style>
