import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

// 路由页面引入
const Login = () => import('@/views/Login.vue')
const Home = () => import('@/views/Home.vue')
const Result = () => import('@/views/Result.vue')
const History = () => import('@/views/History.vue')
const UserCenter = () => import('@/views/UserCenter.vue')
const Help = () => import('@/views/Help.vue')

const routes = [
  {
    path: '/',
    redirect: '/home'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      title: '登录/注册 - 伪科普内容识别系统',
      requiresAuth: false
    }
  },
  {
    path: '/home',
    name: 'Home',
    component: Home,
    meta: {
      title: '首页 - 伪科普内容识别系统',
      requiresAuth: true
    }
  },
  {
    path: '/result/:contentId',
    name: 'Result',
    component: Result,
    meta: {
      title: '识别结果 - 伪科普内容识别系统',
      requiresAuth: true
    }
  },
  {
    path: '/history',
    name: 'History',
    component: History,
    meta: {
      title: '识别历史 - 伪科普内容识别系统',
      requiresAuth: true
    }
  },
  {
    path: '/user-center',
    name: 'UserCenter',
    component: UserCenter,
    meta: {
      title: '个人中心 - 伪科普内容识别系统',
      requiresAuth: true
    }
  },
  {
    path: '/help',
    name: 'Help',
    component: Help,
    meta: {
      title: '帮助中心 - 伪科普内容识别系统',
      requiresAuth: true
    }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/home'
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 路由守卫-登录鉴权
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const token = userStore.token
  document.title = to.meta.title || '伪科普内容识别系统'

  // 需要登录的页面
  if (to.meta.requiresAuth) {
    if (!token) {
      ElMessage.warning('请先登录账号')
      next('/login')
    } else {
      next()
    }
  } else {
    // 登录页已登录状态跳首页
    if (to.path === '/login' && token) {
      next('/home')
    } else {
      next()
    }
  }
})

export default router
