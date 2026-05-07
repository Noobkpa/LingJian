import { createRouter, createWebHistory } from 'vue-router'

// 门户页面
const Portal = () => import('@/views/portal/Index.vue')

// ==================== 用户端路由 ====================
const UserLogin = () => import('@/views/user/Login.vue')
const UserHome = () => import('@/views/user/Home.vue')
const UserHistory = () => import('@/views/user/History.vue')
const UserResult = () => import('@/views/user/Result.vue')
const UserCenter = () => import('@/views/user/UserCenter.vue')
const UserHelp = () => import('@/views/user/Help.vue')

// ==================== 管理端路由（完全匹配你的文件名） ====================
const AdminLogin = () => import('@/views/admin/Login.vue')
const AdminLayout = () => import('@/components/admin/AdminLayout.vue')
const AdminDashboard = () => import('@/views/admin/Dashboard.vue')
const UserManage = () => import('@/views/admin/UserManage.vue')
const ContentAudit = () => import('@/views/admin/ContentAudit.vue')
const SystemConfig = () => import('@/views/admin/SystemConfig.vue') // 修正为你的真实文件名

// ==================== 审核端路由 ====================
const AuditLogin = () => import('@/views/audit/Login.vue')
const AuditLayout = () => import('@/components/audit/AuditLayout.vue')
const AuditTask = () => import('@/views/audit/AuditTask.vue')
const AuditDetail = () => import('@/views/audit/AuditDetail.vue')
const AuditHistory = () => import('@/views/audit/AuditHistory.vue')
const Profile = () => import('@/views/audit/Profile.vue')

const routes = [
  // 门户首页
  {
    path: '/',
    name: 'Portal',
    component: Portal,
    meta: { title: '灵鉴-系统门户' }
  },

  // ==================== 用户端（无布局，直接跳转） ====================
  {
    path: '/user/login',
    name: 'UserLogin',
    component: UserLogin,
    meta: { title: '用户登录' }
  },
  {
    path: '/user/home',
    name: 'UserHome',
    component: UserHome,
    meta: { title: '用户首页' }
  },
  {
    path: '/user/history',
    name: 'UserHistory',
    component: UserHistory,
    meta: { title: '识别历史' }
  },
  {
    path: '/user/result/:contentId',
    name: 'UserResult',
    component: UserResult,
    meta: { title: '识别结果' }
  },
  {
    path: '/user/center',
    name: 'UserCenter',
    component: UserCenter,
    meta: { title: '个人中心' }
  },
  {
    path: '/user/help',
    name: 'UserHelp',
    component: UserHelp,
    meta: { title: '帮助中心' }
  },

  // ==================== 管理端 ====================
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: AdminLogin,
    meta: { title: '管理员登录' }
  },
  {
    path: '/admin',
    component: AdminLayout,
    children: [
      { 
        path: 'dashboard', 
        name: 'AdminDashboard', 
        component: AdminDashboard, 
        meta: { title: '数据看板' }
      },
      { 
        path: 'user', 
        name: 'UserManage', 
        component: UserManage, 
        meta: { title: '用户管理' }
      },
      { 
        path: 'content', 
        name: 'ContentAudit', 
        component: ContentAudit, 
        meta: { title: '内容审核' }
      },
      { 
        path: 'config', 
        name: 'SystemConfig', 
        component: SystemConfig, 
        meta: { title: '系统配置' }
      }
    ]
  },

  // ==================== 审核端 ====================
  {
    path: '/audit/login',
    name: 'AuditLogin',
    component: AuditLogin,
    meta: { title: '审核员登录' }
  },
  {
    path: '/audit',
    component: AuditLayout,
    children: [
      { 
        path: 'task', 
        name: 'AuditTask', 
        component: AuditTask, 
        meta: { title: '审核任务' }
      },
      { 
        path: 'detail/:contentId', 
        name: 'AuditDetail', 
        component: AuditDetail, 
        meta: { title: '审核详情' }
      },
      { 
        path: 'history', 
        name: 'AuditHistory', 
        component: AuditHistory, 
        meta: { title: '审核历史' }
      },
      { 
        path: 'profile', 
        name: 'Profile', 
        component: Profile, 
        meta: { title: '个人中心' }
      }
    ]
  },

  // 404兜底
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router