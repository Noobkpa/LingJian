import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

// 路由页面引入
const Login = () => import('@/views/Login.vue')
const AuditLayout = () => import('@/components/AuditLayout.vue')
const AuditTask = () => import('@/views/AuditTask.vue')
const AuditDetail = () => import('@/views/AuditDetail.vue')
const AuditHistory = () => import('@/views/AuditHistory.vue')
const Profile = () => import('@/views/Profile.vue')

const routes = [
  {
    path: '/',
    redirect: '/audit/task'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      title: '审核员登录 - 专业审核端',
      requiresAuth: false
    }
  },
  {
    path: '/audit',
    component: AuditLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: 'task',
        name: 'AuditTask',
        component: AuditTask,
        meta: {
          title: '审核任务大厅 - 专业审核端',
          requiresAuth: true,
          icon: 'Document'
        }
      },
      {
        path: 'detail/:contentId',
        name: 'AuditDetail',
        component: AuditDetail,
        meta: {
          title: '内容审核详情 - 专业审核端',
          requiresAuth: true,
          hidden: true
        }
      },
      {
        path: 'history',
        name: 'AuditHistory',
        component: AuditHistory,
        meta: {
          title: '我的审核历史 - 专业审核端',
          requiresAuth: true,
          icon: 'Clock'
        }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: Profile,
        meta: {
          title: '个人中心 - 专业审核端',
          requiresAuth: true,
          icon: 'User'
        }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/audit/task'
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 路由守卫-审核员鉴权
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const token = userStore.token
  document.title = to.meta.title || '专业审核端'

  if (to.meta.requiresAuth) {
    if (!token) {
      ElMessage.warning('请先登录审核员账号')
      next('/login')
    } else {
      next()
    }
  } else {
    if (to.path === '/login' && token) {
      next('/audit/task')
    } else {
      next()
    }
  }
})

export default router
