<template>
  <div class="user-center-container">
    <div class="page-header">
      <h2 class="page-title">个人中心</h2>
    </div>

    <el-row :gutter="24">
      <!-- 左侧信息卡片 -->
      <el-col :span="8">
        <div class="user-info-card base-card">
          <div class="user-avatar">
            <el-avatar :size="80" icon="UserFilled" />
          </div>
          <div class="user-base-info">
            <h3 class="username">{{ userInfo.nickname || userInfo.username }}</h3>
            <p class="user-role">普通用户</p>
            <p class="user-id">账号ID：{{ userInfo.user_id }}</p>
          </div>
          <el-divider />
          <div class="user-stats">
            <el-row :gutter="16">
              <el-col :span="8" class="stat-item">
                <div class="stat-num">{{ stats.total_count }}</div>
                <div class="stat-label">总识别数</div>
              </el-col>
              <el-col :span="8" class="stat-item">
                <div class="stat-num">{{ stats.high_risk_count }}</div>
                <div class="stat-label">高风险</div>
              </el-col>
              <el-col :span="8" class="stat-item">
                <div class="stat-num">{{ stats.collect_count }}</div>
                <div class="stat-label">收藏数</div>
              </el-col>
            </el-row>
          </div>
        </div>
      </el-col>

      <!-- 右侧表单区 -->
      <el-col :span="16">
        <el-tabs v-model="activeTab" type="border-card" class="center-tabs">
          <!-- 基本信息 -->
          <el-tab-pane label="基本信息" name="info">
            <el-form
              ref="infoFormRef"
              :model="infoForm"
              :rules="infoRules"
              label-width="100px"
              size="large"
              class="info-form"
            >
              <el-form-item label="登录账号" prop="username">
                <el-input v-model="infoForm.username" disabled />
              </el-form-item>
              <el-form-item label="用户昵称" prop="nickname">
                <el-input v-model="infoForm.nickname" placeholder="请设置昵称" clearable />
              </el-form-item>
              <el-form-item label="手机号" prop="phone">
                <el-input v-model="infoForm.phone" placeholder="请输入手机号" clearable />
              </el-form-item>
              <el-form-item label="注册时间">
                <el-input v-model="infoForm.register_time" disabled />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="infoLoading" @click="updateInfo">保存修改</el-button>
                <el-button @click="resetInfoForm">重置</el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <!-- 修改密码 -->
          <el-tab-pane label="修改密码" name="password">
            <el-form
              ref="passwordFormRef"
              :model="passwordForm"
              :rules="passwordRules"
              label-width="120px"
              size="large"
              class="password-form"
            >
              <el-form-item label="当前密码" prop="oldPassword">
                <el-input
                  v-model="passwordForm.oldPassword"
                  type="password"
                  show-password
                  placeholder="请输入当前密码"
                  clearable
                />
              </el-form-item>
              <el-form-item label="新密码" prop="newPassword">
                <el-input
                  v-model="passwordForm.newPassword"
                  type="password"
                  show-password
                  placeholder="请设置新密码"
                  clearable
                />
              </el-form-item>
              <el-form-item label="确认新密码" prop="confirmPassword">
                <el-input
                  v-model="passwordForm.confirmPassword"
                  type="password"
                  show-password
                  placeholder="请再次确认新密码"
                  clearable
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="passwordLoading" @click="updatePassword">修改密码</el-button>
                <el-button @click="resetPasswordForm">重置</el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <!-- 账号注销 -->
          <el-tab-pane label="账号注销" name="cancel">
            <div class="cancel-card">
              <el-alert
                title="账号注销须知"
                type="warning"
                :closable="false"
                show-icon
                style="margin-bottom: 20px"
              >
                <ul>
                  <li>账号注销后，您的所有个人信息、识别记录、收藏数据将被清空，无法恢复</li>
                  <li>注销操作不可逆，请您务必谨慎操作，提前备份好相关数据</li>
                  <li>账号注销后，该账号将无法再次登录，如需使用需重新注册</li>
                </ul>
              </el-alert>
              <el-button type="danger" @click="handleCancelAccount">注销账号</el-button>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useIdentifyStore } from '@/stores/identify'
import { ElMessageBox, ElMessage } from 'element-plus'
import { phoneRule, passwordRule } from '@/utils/validate'

const router = useRouter()
const userStore = useUserStore()
const identifyStore = useIdentifyStore()

// 状态定义
const activeTab = ref('info')
const infoLoading = ref(false)
const passwordLoading = ref(false)
// 用户信息
const userInfo = computed(() => userStore.userInfo)
const stats = reactive({
  total_count: 0,
  high_risk_count: 0,
  collect_count: 0
})
// 信息表单
const infoFormRef = ref()
const infoForm = reactive({
  username: '',
  nickname: '',
  phone: '',
  register_time: ''
})
const infoRules = {
  nickname: [
    { required: true, message: '请设置昵称', trigger: 'blur' }
  ],
  phone: [
    { validator: phoneRule, trigger: 'blur' }
  ]
}
// 密码表单
const passwordFormRef = ref()
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})
// 确认密码校验
const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}
const passwordRules = {
  oldPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { validator: passwordRule, trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 方法
const initFormData = () => {
  const info = userInfo.value
  infoForm.username = info.username || ''
  infoForm.nickname = info.nickname || ''
  infoForm.phone = info.phone || ''
  infoForm.register_time = info.register_time || ''
}

const resetInfoForm = () => {
  initFormData()
}

const updateInfo = async () => {
  if (!infoFormRef.value) return
  const valid = await infoFormRef.value.validate()
  if (!valid) return

  try {
    infoLoading.value = true
    await userStore.updateUserInfo({
      nickname: infoForm.nickname,
      phone: infoForm.phone
    })
    ElMessage.success('个人信息修改成功')
  } catch (error) {
    console.error('信息修改失败', error)
  } finally {
    infoLoading.value = false
  }
}

const resetPasswordForm = () => {
  passwordFormRef.value?.resetFields()
}

const updatePassword = async () => {
  if (!passwordFormRef.value) return
  const valid = await passwordFormRef.value.validate()
  if (!valid) return

  try {
    passwordLoading.value = true
    await userStore.updatePassword(passwordForm)
    ElMessage.success('密码修改成功，请重新登录')
    userStore.logout()
    router.push('/login')
  } catch (error) {
    console.error('密码修改失败', error)
  } finally {
    passwordLoading.value = false
  }
}

const handleCancelAccount = () => {
  ElMessageBox.confirm(
    '您确定要注销账号吗？注销后所有数据将被清空且无法恢复，此操作不可逆！',
    '账号注销警告',
    {
      confirmButtonText: '确定注销',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger',
      inputType: 'text',
      showInput: true,
      inputPlaceholder: '请输入"注销"确认操作',
      beforeClose: async (action, instance, done) => {
        if (action === 'confirm') {
          if (instance.inputValue !== '注销') {
            ElMessage.error('请输入"注销"确认操作')
            return
          }
          done()
        } else {
          done()
        }
      }
    }
  ).then(async () => {
    await userStore.cancelAccount()
    ElMessage.success('账号已注销')
    router.push('/login')
  }).catch(() => {})
}

const getUserStats = async () => {
  try {
    const res = await identifyStore.getHistoryList({ page: 1, size: 1000 })
    stats.total_count = res.total
    stats.high_risk_count = res.list.filter(item => item.risk_level === 'high').length
    const collectRes = await identifyStore.getCollectList({ page: 1, size: 1000 })
    stats.collect_count = collectRes.total
  } catch (error) {
    console.error('获取用户统计数据失败', error)
  }
}

onMounted(() => {
  initFormData()
  getUserStats()
})
</script>

<style scoped>
.user-center-container {
  width: 100%;
}
.page-header {
  margin-bottom: 20px;
}
.page-title {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin: 0;
}
.user-info-card {
  text-align: center;
}
.user-avatar {
  margin-bottom: 16px;
}
.user-base-info {
  margin-bottom: 16px;
}
.username {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}
.user-role {
  font-size: 14px;
  color: #909399;
  margin-bottom: 4px;
}
.user-id {
  font-size: 12px;
  color: #c0c4cc;
}
.user-stats {
  padding-top: 8px;
}
.stat-item {
  text-align: center;
}
.stat-num {
  font-size: 20px;
  font-weight: bold;
  color: #4080FF;
  margin-bottom: 4px;
}
.stat-label {
  font-size: 12px;
  color: #909399;
}
.center-tabs {
  min-height: 500px;
}
.info-form,
.password-form {
  max-width: 500px;
  padding: 20px 0;
}
.cancel-card {
  padding: 20px 0;
}
.cancel-card ul {
  padding-left: 20px;
  margin: 0;
}
.cancel-card li {
  line-height: 1.8;
  margin-bottom: 8px;
}
</style>