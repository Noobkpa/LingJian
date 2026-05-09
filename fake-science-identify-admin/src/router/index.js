import { createRouter, createWebHistory } from 'vue-router'
import { useAdminStore } from '@/stores/admin'
import { ElMessage } from 'element-plus'

// 路由页面引入
const Login = () => import('@/views/Login.vue')
const AdminLayout = () => import('@/components/AdminLayout.vue')
const Dashboard = () => import('@/views/Dashboard.vue')
const UserManage = () => import('@/views/UserManage.vue')
const ContentAudit = () => import('@/views/ContentAudit.vue')
const ModelManage = () => import('@/views/ModelManage.vue')
const SystemConfig = () => import('@/views/SystemConfig.vue')

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      title: '管理员登录 - 平台管理端',
      requiresAuth: false
    }
  },
  {
    path: '/',
    component: AdminLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: Dashboard,
        meta: {
          title: '数据看板 - 平台管理端',
          requiresAuth: true,
          icon: 'DataBoard'
        }
      },
      {
        path: 'user-manage',
        name: 'UserManage',
        component: UserManage,
        meta: {
          title: '用户管理 - 平台管理端',
          requiresAuth: true,
          icon: 'User'
        }
      },
      {
        path: 'content-audit',
        name: 'ContentAudit',
        component: ContentAudit,
        meta: {
          title: '内容审核 - 平台管理端',
          requiresAuth: true,
          icon: 'Document'
        }
      },
      {
        path: 'model-manage',
        name: 'ModelManage',
        component: ModelManage,
        meta: {
          title: '模型管理 - 平台管理端',
          requiresAuth: true,
          icon: 'Setting'
        }
      },
      {
        path: 'system-config',
        name: 'SystemConfig',
        component: SystemConfig,
        meta: {
          title: '系统配置 - 平台管理端',
          requiresAuth: true,
          icon: 'Tools'
        }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard'
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 路由守卫-管理员鉴权
router.beforeEach((to, from, next) => {
  const adminStore = useAdminStore()
  const token = adminStore.token
  document.title = to.meta.title || '平台管理端'

  if (to.meta.requiresAuth) {
    if (!token) {
      ElMessage.warning('请先登录管理员账号')
      next('/login')
    } else {
      next()
    }
  } else {
    if (to.path === '/login' && token) {
      next('/dashboard')
    } else {
      next()
    }
  }
})

export default router
