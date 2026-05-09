<template>
  <div class="audit-layout">
    <!-- 侧边栏 -->
    <aside class="audit-sidebar">
      <div class="sidebar-logo">
        <h2>灵鉴审核</h2>
      </div>
      <el-menu
        :default-active="activePath"
        class="el-menu-vertical-demo"
        router
      >
        <el-menu-item index="/audit/task">
          <el-icon><Document /></el-icon>
          <span>审核任务</span>
        </el-menu-item>
        <el-menu-item index="/audit/history">
          <el-icon><Clock /></el-icon>
          <span>审核历史</span>
        </el-menu-item>
        <el-menu-item index="/audit/profile">
          <el-icon><User /></el-icon>
          <span>个人中心</span>
        </el-menu-item>
      </el-menu>
    </aside>

    <!-- 主内容区 -->
    <div class="audit-main">
      <!-- 顶部栏 -->
      <header class="audit-header">
        <div class="header-left">
          <h3 class="page-title">{{ currentTitle }}</h3>
        </div>
        <div class="header-right">
          <span class="user-name">{{ displayName }}（{{ roleLabel }}）</span>
          <el-button type="text" @click="handleLogout">退出登录</el-button>
        </div>
      </header>

      <!-- 内容区 -->
      <main class="audit-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Document, Clock, User } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 计算属性
const activePath = computed(() => route.path)
const currentTitle = computed(() => route.meta.title?.split(' - ')[0] || '')
const userInfo = computed(() => userStore.userInfo)
const displayName = computed(() => (
  userInfo.value.nickname ||
  userInfo.value.username ||
  '审核员'
))
const roleLabel = computed(() => {
  const label = userInfo.value.role_label
  if (label) return label
  const roles = userInfo.value.roles || []
  if (roles.includes('reviewer')) return '审核员'
  return '审核员'
})

// 退出登录
const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    userStore.logout()
    ElMessage.success('退出登录成功')
    router.push('/login')
  }).catch(() => {})
}
</script>

<style scoped>
.sidebar-logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #409eff;
}
.sidebar-logo h2 {
  color: #fff;
  font-size: 18px;
  margin: 0;
}
.header-left {
  flex: 1;
}
.page-title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  margin: 0;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.user-name {
  font-size: 14px;
  color: #606266;
}
</style>
