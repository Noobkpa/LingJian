<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1 class="logo">灵鉴</h1>
        <p class="logo-desc">专业审核端</p>
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
            placeholder="请输入审核员账号"
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
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/audit/user'
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
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-box {
  width: 380px;
  background: #fff;
  border-radius: 8px;
  padding: 40px 32px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}
.login-header {
  text-align: center;
  margin-bottom: 32px;
}
.logo {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin: 0;
}
.logo-desc {
  font-size: 14px;
  color: #909399;
  margin: 8px 0 0 0;
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
  border: 1px solid #cfe4ff;
  border-radius: 6px;
  color: #409eff;
  background: #f1f7ff;
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
  color: #409eff;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.12);
}
@media (max-width: 460px) {
  .captcha-row {
    grid-template-columns: 1fr;
  }
}
</style>
