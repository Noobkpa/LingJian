<template>
  <div class="login-page">
    <div class="login-bg" aria-hidden="true">
      <div class="login-bg__glow login-bg__glow--1" />
      <div class="login-bg__glow login-bg__glow--2" />
      <div class="login-bg__glow login-bg__glow--3" />
      <div class="login-bg__grid" />
    </div>

    <div class="login-shell">
      <section class="login-hero">
        <div class="login-hero__badge">
          <el-icon class="login-hero__badge-icon"><View /></el-icon>
          <span>科学传播 · 可信守护</span>
        </div>
        <h2 class="login-hero__title">
          灵鉴
          <span class="login-hero__title-sub">Lingjian</span>
        </h2>
        <p class="login-hero__lead">
          伪科普内容识别与风险提示，辅助公众辨别不实「科普」，守护严谨的科学对话。
        </p>
        <ul class="login-hero__features">
          <li><el-icon><CircleCheck /></el-icon>多模态识别 · 文本与图像</li>
          <li><el-icon><CircleCheck /></el-icon>可解释结果 · 依据清晰</li>
          <li><el-icon><CircleCheck /></el-icon>历史留痕 · 随时复核</li>
        </ul>
      </section>

      <div class="login-card">
        <header class="login-card__head">
          <h1 class="login-card__logo">欢迎回来</h1>
          <p class="login-card__desc">登录或注册以使用伪科普识别服务</p>
        </header>

        <el-tabs v-model="activeTab" class="login-tabs">
          <el-tab-pane label="登录" name="login">
            <el-form
              ref="loginFormRef"
              :model="loginForm"
              :rules="loginRules"
              size="large"
              label-width="0"
              class="login-form"
              @submit.prevent
            >
              <el-form-item prop="username">
                <el-input
                  v-model="loginForm.username"
                  placeholder="账号"
                  :prefix-icon="User"
                  clearable
                />
              </el-form-item>
              <el-form-item prop="password">
                <el-input
                  v-model="loginForm.password"
                  type="password"
                  placeholder="密码"
                  :prefix-icon="Lock"
                  show-password
                  clearable
                  @keyup.enter="handleLogin"
                />
              </el-form-item>
              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  class="login-submit"
                  :loading="loading"
                  native-type="submit"
                  @click="handleLogin"
                >
                  登 录
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="注册" name="register">
            <el-form
              ref="registerFormRef"
              :model="registerForm"
              :rules="registerRules"
              size="large"
              label-width="0"
              class="register-form"
              @submit.prevent
            >
              <el-form-item prop="username">
                <el-input
                  v-model="registerForm.username"
                  placeholder="登录账号（4–20 位）"
                  :prefix-icon="User"
                  clearable
                />
              </el-form-item>
              <el-form-item prop="nickname">
                <el-input
                  v-model="registerForm.nickname"
                  placeholder="昵称"
                  :prefix-icon="UserFilled"
                  clearable
                />
              </el-form-item>
              <el-form-item prop="phone">
                <el-input
                  v-model="registerForm.phone"
                  placeholder="手机号"
                  :prefix-icon="Phone"
                  clearable
                />
              </el-form-item>
              <el-form-item prop="password">
                <el-input
                  v-model="registerForm.password"
                  type="password"
                  placeholder="密码"
                  :prefix-icon="Lock"
                  show-password
                  clearable
                />
              </el-form-item>
              <el-form-item prop="confirmPassword">
                <el-input
                  v-model="registerForm.confirmPassword"
                  type="password"
                  placeholder="确认密码"
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
                  class="login-submit"
                  :loading="loading"
                  @click="handleRegister"
                >
                  注 册
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { User, Lock, UserFilled, Phone, View, CircleCheck } from '@element-plus/icons-vue'
import { phoneRule, passwordRule } from '@/utils/validate'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('login')
const loading = ref(false)
const loginFormRef = ref()
const loginForm = reactive({
  username: '',
  password: ''
})
const loginRules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能少于8位', trigger: 'blur' }
  ]
}

const registerFormRef = ref()
const registerForm = reactive({
  username: '',
  nickname: '',
  phone: '',
  password: '',
  confirmPassword: ''
})

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
  nickname: [{ required: true, message: '请设置昵称', trigger: 'blur' }],
  phone: [{ validator: phoneRule, trigger: 'blur' }],
  password: [{ validator: passwordRule, trigger: 'blur' }],
  confirmPassword: [
    { required: true, message: '请再次确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  const valid = await loginFormRef.value.validate()
  if (!valid) return

  try {
    loading.value = true
    await userStore.login(loginForm)
    ElMessage.success('登录成功')
    router.push('/home')
  } catch (error) {
    console.error('登录失败', error)
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  if (!registerFormRef.value) return
  const valid = await registerFormRef.value.validate()
  if (!valid) return

  try {
    loading.value = true
    await userStore.register(registerForm)
    ElMessage.success('注册成功')
    router.push('/home')
    registerFormRef.value.resetFields()
  } catch (error) {
    console.error('注册失败', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  position: relative;
  min-height: 100vh;
  width: 100%;
  overflow-x: hidden;
  display: flex;
  align-items: stretch;
  justify-content: center;
  background: #0c1222;
}

.login-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.login-bg__glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.55;
}
.login-bg__glow--1 {
  width: 420px;
  height: 420px;
  top: -120px;
  right: 10%;
  background: radial-gradient(circle, #4080ff 0%, transparent 70%);
}
.login-bg__glow--2 {
  width: 360px;
  height: 360px;
  bottom: -80px;
  left: 5%;
  background: radial-gradient(circle, #6366f1 0%, transparent 70%);
  opacity: 0.4;
}
.login-bg__glow--3 {
  width: 280px;
  height: 280px;
  top: 40%;
  left: 35%;
  background: radial-gradient(circle, #22d3ee 0%, transparent 70%);
  opacity: 0.25;
}

.login-bg__grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse 80% 70% at 50% 40%, black 20%, transparent 100%);
}

.login-shell {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 1040px;
  margin: auto;
  padding: 48px 24px 56px;
  display: grid;
  grid-template-columns: 1fr 420px;
  gap: 48px;
  align-items: center;
}

@media (max-width: 900px) {
  .login-shell {
    grid-template-columns: 1fr;
    max-width: 440px;
    padding-top: 32px;
  }
  .login-hero {
    text-align: center;
    padding-bottom: 8px;
  }
  .login-hero__features {
    display: none;
  }
}

.login-hero {
  color: #e8edf7;
  padding-right: 16px;
  animation: fade-up 0.6s ease-out both;
}

.login-hero__badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 13px;
  color: #a5b4fc;
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(165, 180, 252, 0.25);
  margin-bottom: 24px;
}
.login-hero__badge-icon {
  font-size: 16px;
}

.login-hero__title {
  font-size: clamp(2.25rem, 4vw, 3rem);
  font-weight: 800;
  letter-spacing: 0.08em;
  margin: 0 0 12px;
  line-height: 1.15;
  background: linear-gradient(135deg, #fff 0%, #c7d7ff 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.login-hero__title-sub {
  display: block;
  font-size: 0.45em;
  font-weight: 600;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: rgba(199, 215, 255, 0.55);
  margin-top: 8px;
  -webkit-text-fill-color: rgba(199, 215, 255, 0.55);
}

.login-hero__lead {
  font-size: 15px;
  line-height: 1.75;
  color: rgba(232, 237, 247, 0.72);
  margin: 0 0 28px;
  max-width: 36em;
}

.login-hero__features {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  font-size: 14px;
  color: rgba(232, 237, 247, 0.85);
}
.login-hero__features li {
  display: flex;
  align-items: center;
  gap: 10px;
}
.login-hero__features .el-icon {
  color: #4ade80;
  font-size: 18px;
}

.login-card {
  animation: fade-up 0.55s ease-out 0.08s both;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 36px 32px 32px;
  box-shadow:
    0 4px 24px rgba(15, 23, 42, 0.08),
    0 0 0 1px rgba(255, 255, 255, 0.6) inset;
}

.login-card__head {
  text-align: center;
  margin-bottom: 8px;
}

.login-card__logo {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 8px;
  letter-spacing: 0.02em;
}

.login-card__desc {
  font-size: 13px;
  color: #64748b;
  margin: 0;
}

.login-tabs {
  --el-tabs-header-height: 44px;
}

.login-tabs :deep(.el-tabs__header) {
  margin-bottom: 22px;
}

.login-tabs :deep(.el-tabs__nav-wrap)::after {
  display: none;
}

.login-tabs :deep(.el-tabs__nav) {
  width: 100%;
  display: flex;
  border-radius: 12px;
  padding: 4px;
  background: #f1f5f9;
}

.login-tabs :deep(.el-tabs__item) {
  flex: 1;
  text-align: center;
  height: 40px;
  line-height: 40px;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  color: #64748b;
  transition: color 0.2s, background 0.2s;
}

.login-tabs :deep(.el-tabs__item.is-active) {
  color: #fff;
  background: linear-gradient(135deg, #4080ff 0%, #5b8cff 100%);
  box-shadow: 0 4px 14px rgba(64, 128, 255, 0.35);
}

.login-tabs :deep(.el-tabs__active-bar) {
  display: none;
}

.login-form,
.register-form {
  padding-top: 4px;
}

.login-form :deep(.el-input__wrapper),
.register-form :deep(.el-input__wrapper) {
  border-radius: 12px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
  transition: box-shadow 0.2s;
}

.login-form :deep(.el-input__wrapper.is-focus),
.register-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #4080ff, 0 0 0 4px rgba(64, 128, 255, 0.12);
}

.login-submit {
  width: 100%;
  height: 46px;
  border-radius: 12px;
  font-weight: 600;
  letter-spacing: 0.12em;
  border: none;
  background: linear-gradient(135deg, #4080ff 0%, #5b8cff 100%);
  box-shadow: 0 8px 24px rgba(64, 128, 255, 0.35);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.login-submit:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 28px rgba(64, 128, 255, 0.42);
}

@keyframes fade-up {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
