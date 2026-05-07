<template>
  <div class="profile-container">
    <h2 class="page-title">个人中心</h2>

    <el-row :gutter="20">
      <!-- 左侧：个人信息 -->
      <el-col :span="10">
        <div class="base-card">
          <h3 class="card-title">个人信息</h3>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="审核员账号">
              {{ userInfo.username }}
            </el-descriptions-item>
            <el-descriptions-item label="真实姓名">
              {{ userInfo.real_name }}
            </el-descriptions-item>
            <el-descriptions-item label="审核等级">
              <el-tag type="warning">{{ userInfo.level }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="联系电话">
              {{ userInfo.phone }}
            </el-descriptions-item>
            <el-descriptions-item label="加入时间">
              {{ userInfo.join_time }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-col>

      <!-- 右侧：审核统计 -->
      <el-col :span="14">
        <div class="base-card">
          <h3 class="card-title">审核统计</h3>
          <el-row :gutter="16">
            <el-col :span="12">
              <div class="stat-item">
                <p class="stat-label">累计审核量</p>
                <p class="stat-value">{{ userInfo.audit_count }}</p>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="stat-item">
                <p class="stat-label">审核准确率</p>
                <p class="stat-value">{{ userInfo.accuracy }}%</p>
              </div>
            </el-col>
          </el-row>
        </div>

        <div class="base-card">
          <h3 class="card-title">修改密码</h3>
          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            label-width="100px"
            style="max-width: 500px"
          >
            <el-form-item label="原密码" prop="old_password">
              <el-input v-model="passwordForm.old_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input v-model="passwordForm.new_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirm_password">
              <el-input v-model="passwordForm.confirm_password" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleUpdatePassword">修改密码</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useUserStore } from '@/stores/audit/user'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()

const passwordFormRef = ref()
const userInfo = computed(() => userStore.userInfo)

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  old_password: [
    { required: true, message: '请输入原密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const handleUpdatePassword = async () => {
  if (!passwordFormRef.value) return
  const valid = await passwordFormRef.value.validate()
  if (!valid) return

  try {
    ElMessage.success('密码修改成功')
    passwordFormRef.value.resetFields()
  } catch (error) {
    console.error('修改失败', error)
  }
}
</script>

<style scoped>
.profile-container {
  width: 100%;
}
.page-title {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 20px 0;
}
.card-title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 16px 0;
}
.stat-item {
  text-align: center;
  padding: 24px;
  background: #f5f7fa;
  border-radius: 8px;
}
.stat-label {
  font-size: 14px;
  color: #606266;
  margin: 0 0 8px 0;
}
.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin: 0;
}
</style>