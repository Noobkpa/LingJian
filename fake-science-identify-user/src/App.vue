<template>
  <div id="app">
    <CommonHeader v-if="!isLoginPage" />
    <main class="main-container" :class="{ 'main-container--login': isLoginPage }">
      <router-view />
    </main>
    <CommonFooter v-if="!isLoginPage" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import CommonHeader from '@/components/CommonHeader.vue'
import CommonFooter from '@/components/CommonFooter.vue'

const route = useRoute()
// 判断是否为登录页，隐藏头部底部
const isLoginPage = computed(() => route.path === '/login')
</script>

<style scoped>
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f7fa;
}
.main-container {
  flex: 1;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px 16px;
}
.main-container--login {
  max-width: none;
  width: 100%;
  margin: 0;
  padding: 0;
  flex: 1;
  min-height: 0;
}
</style>