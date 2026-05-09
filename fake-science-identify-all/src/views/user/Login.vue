<template>
  <div class="login-page">
    <div class="login-shell">
      <section class="login-hero">
        <div class="brand-lockup">
          <span class="brand-mark">灵</span>
          <span class="brand-name">灵鉴</span>
        </div>
        <div class="login-hero__badge">
          <el-icon class="login-hero__badge-icon"><View /></el-icon>
          <span>Public Science Risk Check</span>
        </div>
        <h2 class="login-hero__title">
          灵鉴
          <span class="login-hero__title-sub">Lingjian</span>
        </h2>
        <p class="login-hero__lead">
          面向公众的伪科普识别服务。提交文本或图片，获得风险等级、依据说明与可复核建议。
        </p>
        <ul class="login-hero__features">
          <li><el-icon><CircleCheck /></el-icon>文本、截图与图文混合识别</li>
          <li><el-icon><CircleCheck /></el-icon>风险理由、证据边界与行动建议</li>
          <li><el-icon><CircleCheck /></el-icon>登录后保存历史，便于后续复查</li>
        </ul>
        <div class="hero-note">
          <span>AI 初判</span>
          <span>人工复核</span>
          <span>权威求证</span>
        </div>
      </section>

      <div class="login-card">
        <header class="login-card__head">
          <p class="login-card__eyebrow">公众用户入口</p>
          <h1 class="login-card__logo">登录灵鉴</h1>
          <p class="login-card__desc">继续识别内容风险，或创建账号保存你的识别记录。</p>
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
                  class="login-submit"
                  :loading="loading"
                  native-type="submit"
                  @click="handleLogin"
                >
                  登录
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
                  注册
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
import { onMounted, ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user/user'
import { ElMessage } from 'element-plus'
import { User, Lock, UserFilled, Phone, View, CircleCheck, RefreshRight } from '@element-plus/icons-vue'
import { phoneRule, passwordRule } from '@/utils/validate'
import request from '@/utils/request'
import { V1 } from '@/api/v1/endpoints'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('login')
const loading = ref(false)
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
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
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

const handleRegister = async () => {
  if (!registerFormRef.value) return
  const valid = await registerFormRef.value.validate()
  if (!valid) return

  try {
    loading.value = true
    await userStore.register(registerForm)
    ElMessage.success('注册成功')
    router.push('/user/home')
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
.login-page {
  position: relative;
  min-height: 100vh;
  width: 100%;
  overflow-x: hidden;
  display: flex;
  align-items: stretch;
  justify-content: center;
  background:
    linear-gradient(120deg, rgba(10, 27, 35, 0.94), rgba(28, 87, 82, 0.72)),
    url('https://images.unsplash.com/photo-1581093458791-9d42e4e4dc46?auto=format&fit=crop&w=1800&q=80') center/cover;
}

.login-page::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px),
    linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px);
  background-size: 72px 72px;
  opacity: 0.26;
}

.login-shell {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 1120px;
  margin: auto;
  padding: 48px 24px 56px;
  display: grid;
  grid-template-columns: minmax(420px, 1fr) 430px;
  gap: 64px;
  align-items: center;
}

@media (max-width: 900px) {
  .login-shell {
    grid-template-columns: 1fr;
    max-width: 440px;
    padding-top: 32px;
    gap: 28px;
  }
  .login-hero {
    text-align: center;
    padding-bottom: 8px;
  }
  .login-hero__features {
    display: none;
  }
  .brand-lockup,
  .hero-note {
    justify-content: center;
  }
  .login-hero__title {
    font-size: 36px;
  }
  .login-card {
    padding: 34px 24px 28px;
  }
}

.login-hero {
  color: #f5f8fb;
  padding-right: 16px;
  animation: fade-up 0.6s ease-out both;
}

.brand-lockup {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 34px;
}

.brand-mark {
  display: inline-flex;
  width: 38px;
  height: 38px;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.94);
  color: #177b74;
  font-weight: 800;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.18);
}

.brand-name {
  color: rgba(255, 255, 255, 0.92);
  font-size: 18px;
  font-weight: 700;
}

.login-hero__badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  border-radius: 4px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.86);
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.24);
  margin-bottom: 22px;
}
.login-hero__badge-icon {
  font-size: 16px;
}

.login-hero__title {
  font-size: 52px;
  font-weight: 800;
  letter-spacing: 0;
  margin: 0 0 12px;
  line-height: 1.15;
  color: #fff;
}

.login-hero__title-sub {
  display: block;
  font-size: 0.45em;
  font-weight: 600;
  letter-spacing: 0;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.58);
  margin-top: 8px;
}

.login-hero__lead {
  font-size: 17px;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.82);
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
  color: rgba(255, 255, 255, 0.86);
}
.login-hero__features li {
  display: flex;
  align-items: center;
  gap: 10px;
}
.login-hero__features .el-icon {
  color: #9dd8c8;
  font-size: 18px;
}

.hero-note {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 34px;
}

.hero-note span {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.86);
  font-size: 13px;
}

.login-card {
  position: relative;
  overflow: hidden;
  animation: fade-up 0.55s ease-out 0.08s both;
  background: #fff;
  border-radius: 8px;
  padding: 40px 34px 32px;
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.22);
}

.login-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 4px;
  background: linear-gradient(90deg, #177b74, #e0a94f);
}

.login-card__head {
  text-align: left;
  margin-bottom: 8px;
}

.login-card__eyebrow {
  margin: 0 0 8px;
  color: #177b74;
  font-size: 13px;
}

.login-card__logo {
  font-size: 26px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 8px;
  letter-spacing: 0;
}

.login-card__desc {
  font-size: 13px;
  color: #64748b;
  margin: 0;
  line-height: 1.7;
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
  border-radius: 6px;
  padding: 4px;
  background: #eef4f3;
}

.login-tabs :deep(.el-tabs__item) {
  flex: 1;
  text-align: center;
  height: 40px;
  line-height: 40px;
  border: none;
  border-radius: 4px;
  font-weight: 600;
  color: #64748b;
  transition: color 0.2s, background 0.2s;
}

.login-tabs :deep(.el-tabs__item.is-active) {
  color: #fff;
  background: #177b74;
  box-shadow: 0 4px 14px rgba(23, 123, 116, 0.22);
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
  border-radius: 6px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
  transition: box-shadow 0.2s;
}

.login-form :deep(.el-input__wrapper.is-focus),
.register-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #177b74, 0 0 0 4px rgba(23, 123, 116, 0.12);
}

.login-submit {
  width: 100%;
  height: 46px;
  border-radius: 6px;
  font-weight: 600;
  letter-spacing: 0;
  border: none;
  background: #177b74;
  box-shadow: 0 8px 24px rgba(23, 123, 116, 0.28);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.login-submit:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 28px rgba(23, 123, 116, 0.34);
}

.login-submit:active {
  transform: translateY(0);
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
  border-radius: 6px;
  color: #177b74;
  background: #eef8f6;
  border: 1px solid #cce7e2;
  border-color: #cce7e2;
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
  color: #177b74;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.12);
}

@media (max-width: 420px) {
  .captcha-row {
    grid-template-columns: 1fr;
  }
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
