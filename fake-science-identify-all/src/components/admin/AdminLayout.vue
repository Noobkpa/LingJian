<template>
  <div class="admin-layout">
    <!-- 侧边栏 -->
    <aside class="admin-sidebar">
      <div class="sidebar-logo">
        <h2>灵鉴管理端</h2>
      </div>
      <el-menu
        :default-active="activePath"
        class="sidebar-menu"
        background-color="#001529"
        text-color="#fff"
        active-text-color="#fff"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
          <span>数据看板</span>
        </el-menu-item>
        <el-menu-item index="/user-manage">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/content-audit">
          <el-icon><Document /></el-icon>
          <span>内容审核</span>
        </el-menu-item>
        <el-menu-item index="/model-manage">
          <el-icon><Setting /></el-icon>
          <span>模型管理</span>
        </el-menu-item>
        <el-menu-item index="/system-config">
          <el-icon><Tools /></el-icon>
          <span>系统配置</span>
        </el-menu-item>
      </el-menu>
    </aside>

    <!-- 主内容区 -->
    <div class="admin-main">
      <!-- 顶部栏 -->
      <header class="admin-header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentTitle">{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <span class="admin-name">欢迎，{{ adminInfo.username }}</span>
          <el-button type="text" @click="handleLogout">退出登录</el-button>
        </div>
      </header>

      <!-- 内容区 -->
      <main class="admin-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAdminStore } from '@/stores/admin/admin'
import { ElMessageBox, ElMessage } from 'element-plus'
import { DataBoard, User, Document, Setting, Tools } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const adminStore = useAdminStore()

// 计算属性
const activePath = computed(() => route.path)
const currentTitle = computed(() => route.meta.title?.split(' - ')[0] || '')
const adminInfo = computed(() => adminStore.adminInfo)

// 退出登录
const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    adminStore.logout()
    ElMessage.success('退出登录成功')
    router.push('/admin/login')
  }).catch(() => {})
}
</script>

<style scoped>
.sidebar-logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000c17;
}
.sidebar-logo h2 {
  color: #fff;
  font-size: 18px;
  margin: 0;
}
.sidebar-menu {
  border-right: none;
}
.header-left {
  flex: 1;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.admin-name {
  font-size: 14px;
  color: #303133;
}
</style>