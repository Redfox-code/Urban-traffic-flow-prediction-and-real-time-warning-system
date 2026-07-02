import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'

const routes = [
  { path: '/login', name: 'Login', component: () => import('@/views/Login.vue'), meta: { title: '登录' } },
  { path: '/register', name: 'Register', component: () => import('@/views/Register.vue'), meta: { title: '注册' } },
  {
    path: '/', component: () => import('@/layouts/MainLayout.vue'), meta: { requiresAuth: true },
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/Dashboard.vue'), meta: { title: '系统首页' } },
      { path: 'traffic', name: 'TrafficMonitor', component: () => import('@/views/TrafficMonitor.vue'), meta: { title: '实时路况' } },
      { path: 'prediction', name: 'PredictionBoard', component: () => import('@/views/PredictionBoard.vue'), meta: { title: '流量预测' } },
      { path: 'warnings', name: 'WarningManager', component: () => import('@/views/WarningManager.vue'), meta: { title: '预警管理' } },
      { path: 'route-plan', name: 'RoutePlanner', component: () => import('@/views/RoutePlanner.vue'), meta: { title: '路径规划' } },
      { path: 'admin/users', name: 'UserManager', component: () => import('@/views/admin/UserManager.vue'), meta: { title: '用户管理', role: 'admin' } },
      { path: 'admin/logs', name: 'SystemLogs', component: () => import('@/views/admin/SystemLogs.vue'), meta: { title: '系统日志', role: 'admin' } },
    ],
  },
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('@/views/NotFound.vue'), meta: { title: '404' } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} | 智能交通系统` : '智能交通系统'
  const userStore = useUserStore()
  if (to.meta.requiresAuth && !userStore.token) return next({ name: 'Login', query: { redirect: to.fullPath } })
  if (to.meta.role === 'admin' && userStore.role !== 'admin') return next({ name: 'Dashboard' })
  if ((to.name === 'Login' || to.name === 'Register') && userStore.token) return next({ name: 'Dashboard' })
  next()
})

export default router
