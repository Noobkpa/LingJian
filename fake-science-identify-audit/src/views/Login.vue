<template>
  <div class="login-container">
    <section class="login-intro" aria-label="灵鉴专家复核工作台">
      <div class="brand-lockup">
        <span class="brand-mark">灵</span>
        <span class="brand-name">灵鉴</span>
      </div>
      <p class="eyebrow">LingJian Review Workspace</p>
      <h1>灵鉴专家复核工作台</h1>
      <p class="intro-text">
        面向审核员与专家协作者的公网入口，用于复核待审内容、沉淀人工结论并校准 AI 研判结果。
      </p>
      <div class="trust-list">
        <span>实名协作</span>
        <span>复核留痕</span>
        <span>人机协同</span>
      </div>
    </section>
    <div class="login-box">
      <div class="login-header">
        <p class="logo-desc">审核员身份验证</p>
        <h2 class="logo">进入复核工作台</h2>
        <p class="login-note">请使用平台分配的审核员账号登录。公网访问请确认当前网络环境可信。</p>
      </div>
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
            placeholder="审核员账号"
            :prefix-icon="User"
            clearable
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="登录密码"
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
            安全登录
          </el-button>
        </el-form-item>
      </el-form>
      <p class="access-tip">仅限授权审核员访问。若账号权限异常，请联系平台管理员。</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { User, Lock, RefreshRight } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { V1 } from '@/api/v1/endpoints'

const router = useRouter()
const userStore = useUserStore()

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
  username: [
    { required: true, message: '请输入审核员账号', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
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

const handleLogin = async () => {
  if (!loginFormRef.value) return
  const valid = await loginFormRef.value.validate()
  if (!valid) return

  try {
    loading.value = true
    if (!loginForm.captcha_id) await refreshCaptcha()
    await userStore.login(loginForm)
    ElMessage.success('登录成功')
    router.push('/audit/task')
  } catch (error) {
    console.error('登录失败', error)
    await refreshCaptcha()
  } finally {
    loading.value = false
  }
}

onMounted(refreshCaptcha)
</script>

<style scoped>
.login-container {
  position: relative;
  width: 100vw;
  height: 100vh;
  min-height: 640px;
  background:
    linear-gradient(120deg, rgba(12, 31, 38, 0.92), rgba(20, 114, 105, 0.84)),
    url('https://images.unsplash.com/photo-1551836022-d5d88e9218df?auto=format&fit=crop&w=1800&q=80') center/cover;
  display: grid;
  grid-template-columns: minmax(320px, 560px) minmax(360px, 420px);
  align-items: center;
  justify-content: center;
  gap: 72px;
  padding: 48px;
  box-sizing: border-box;
}
.login-container::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px),
    linear-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px);
  background-size: 72px 72px;
  opacity: 0.24;
}
.login-intro {
  position: relative;
  z-index: 1;
  color: #fff;
  max-width: 560px;
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
  color: #178276;
  font-weight: 800;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.18);
}
.brand-name {
  color: rgba(255, 255, 255, 0.92);
  font-size: 18px;
  font-weight: 700;
}
.eyebrow {
  margin: 0 0 16px;
  color: rgba(255, 255, 255, 0.72);
  font-size: 13px;
}
.login-intro h1 {
  margin: 0;
  font-size: 44px;
  line-height: 1.16;
  font-weight: 700;
}
.intro-text {
  margin: 18px 0 0;
  max-width: 520px;
  color: rgba(255, 255, 255, 0.84);
  font-size: 17px;
  line-height: 1.8;
}
.trust-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 28px;
}
.trust-list span {
  padding: 8px 12px;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.86);
  background: rgba(255, 255, 255, 0.08);
  font-size: 13px;
}
.login-box {
  position: relative;
  z-index: 1;
  overflow: hidden;
  width: 100%;
  background: #fff;
  border-radius: 8px;
  padding: 40px 34px 30px;
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.24);
}
.login-box::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 4px;
  background: linear-gradient(90deg, #178276, #e0a94f);
}
.login-header {
  margin-bottom: 28px;
}
.logo {
  font-size: 26px;
  line-height: 1.3;
  font-weight: 700;
  color: #172033;
  margin: 6px 0 0;
}
.logo-desc {
  font-size: 13px;
  color: #178276;
  margin: 0;
}
.login-note {
  margin: 12px 0 0;
  color: #6b7280;
  font-size: 14px;
  line-height: 1.7;
}
.login-form {
  padding-top: 8px;
}
.login-form :deep(.el-input__wrapper) {
  border-radius: 6px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}
.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #178276, 0 0 0 4px rgba(23, 130, 118, 0.12);
}
.login-form :deep(.el-button) {
  height: 46px;
  border-radius: 6px;
  font-weight: 600;
  background: #178276;
  border-color: #178276;
  box-shadow: 0 8px 24px rgba(23, 130, 118, 0.26);
}
.login-form :deep(.el-button:hover) {
  background: #116d63;
  border-color: #116d63;
  box-shadow: 0 12px 28px rgba(23, 130, 118, 0.32);
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
  color: #178276;
  background: #eef8f6;
  border: 1px solid #cce7e2;
  border-color: #cce7e2;
  font-weight: 700;
  box-shadow: none !important;
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
  color: #178276;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.12);
}
.access-tip {
  margin: 12px 0 0;
  color: #8a94a6;
  font-size: 12px;
  line-height: 1.6;
}

@media (max-width: 900px) {
  .login-container {
    grid-template-columns: 1fr;
    gap: 28px;
    min-height: 100vh;
    padding: 28px 18px;
  }
  .login-intro {
    max-width: 420px;
  }
  .brand-lockup {
    margin-bottom: 20px;
  }
  .login-intro h1 {
    font-size: 30px;
  }
  .intro-text {
    font-size: 15px;
  }
  .login-box {
    max-width: 420px;
  }
  .captcha-row {
    grid-template-columns: 1fr;
  }
}
</style>
