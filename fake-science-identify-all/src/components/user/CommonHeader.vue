<template>
  <header class="header-container">
    <div class="header-content">
      <div class="logo-area" @click="goHome">
        <span class="logo-text">灵鉴</span>
        <span class="logo-desc">伪科普内容识别系统</span>
      </div>
      <nav class="nav-menu">
        <el-menu
          :default-active="activePath"
          mode="horizontal"
          :ellipsis="false"
          background-color="transparent"
          text-color="#303133"
          active-text-color="#4080FF"
          router
        >
          <el-menu-item index="/user/home">首页识别</el-menu-item>
          <el-menu-item index="/user/history">识别历史</el-menu-item>
          <el-menu-item index="/user/help">帮助中心</el-menu-item>
        </el-menu>
      </nav>
      <div class="user-area">
        <el-dropdown @command="handleCommand">
          <div class="user-info">
            <el-avatar :size="32" icon="UserFilled" />
            <span class="username">{{ userInfo.nickname || userInfo.username }}</span>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="center">个人中心</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user/user'
import { ElMessageBox, ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 计算属性
const activePath = computed(() => route.path)
const userInfo = computed(() => userStore.userInfo)

// 方法
const goHome = () => {
  router.push('/user/home')
}

const handleCommand = (command) => {
  switch (command) {
    case 'center':
      router.push('/user/center')
      break
    case 'logout':
      ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        userStore.logout()
        ElMessage.success('退出登录成功')
        router.push('/user/login')
      }).catch(() => {})
      break
  }
}
</script>

<style scoped>
.header-container {
  width: 100%;
  height: 64px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 0;
  z-index: 999;
}
.header-content {
  max-width: 1200px;
  height: 100%;
  margin: 0 auto;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.logo-area {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.logo-text {
  font-size: 24px;
  font-weight: bold;
  color: #4080FF;
}
.logo-desc {
  font-size: 14px;
  color: #909399;
  padding-left: 8px;
  border-left: 1px solid #ebeef5;
}
.nav-menu {
  flex: 1;
  display: flex;
  justify-content: center;
}
.nav-menu :deep(.el-menu) {
  border-bottom: none;
}
.user-area {
  min-width: 120px;
  display: flex;
  justify-content: flex-end;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.username {
  font-size: 14px;
  color: #303133;
}
</style>