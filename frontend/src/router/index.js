import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'
import { getRoleFromToken } from '@/utils/jwt'

// ===== 角色首页映射 =====
const roleHomeMap = {
  admin: { name: 'AdminDashboard' },
  analyst: { name: 'AnalystModels' },
  traveler: { name: 'TravelerRoutePlan' },
}

const routes = [
  // ===== 公开页面 =====
  { path: '/login', name: 'Login', component: () => import('@/views/Login.vue'), meta: { title: '登录' } },
  { path: '/register', name: 'Register', component: () => import('@/views/Register.vue'), meta: { title: '注册' } },

  // ===== 旧版布局（向后兼容） =====
  {
    path: '/', component: () => import('@/layouts/MainLayout.vue'), meta: { requiresAuth: true },
    redirect: '/',
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

  // ===== 管理员布局 =====
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { role: 'admin' },
    redirect: '/admin/dashboard',
    children: [
      { path: 'dashboard', name: 'AdminDashboard', component: () => import('@/views/admin/DashboardView.vue'), meta: { title: '实时监控' } },
      { path: 'warnings', name: 'AdminWarnings', component: () => import('@/views/admin/WarningsView.vue'), meta: { title: '预警管理' } },
      { path: 'signal-optimization', name: 'AdminSignalOpt', component: () => import('@/views/admin/SignalOptimizationView.vue'), meta: { title: '信号优化' } },
      { path: 'emergency', name: 'AdminEmergency', component: () => import('@/views/admin/EmergencyView.vue'), meta: { title: '应急调度' } },
      { path: 'reports', name: 'AdminReports', component: () => import('@/views/admin/ReportsView.vue'), meta: { title: '统计报表' } },
    ],
  },

  // ===== 分析员布局 =====
  {
    path: '/analyst',
    component: () => import('@/layouts/AnalystLayout.vue'),
    meta: { role: 'analyst' },
    redirect: '/analyst/models',
    children: [
      { path: 'models', name: 'AnalystModels', component: () => import('@/views/analyst/ModelsView.vue'), meta: { title: '模型管理' } },
      { path: 'propagation', name: 'AnalystPropagation', component: () => import('@/views/analyst/PropagationView.vue'), meta: { title: '拥堵传播' } },
      { path: 'carbon', name: 'AnalystCarbon', component: () => import('@/views/analyst/CarbonView.vue'), meta: { title: '碳排放' } },
      { path: 'explore', name: 'AnalystExplore', component: () => import('@/views/analyst/ExploreView.vue'), meta: { title: '数据探索' } },
      { path: 'scenarios', name: 'AnalystScenarios', component: () => import('@/views/analyst/ScenariosView.vue'), meta: { title: '场景仿真' } },
    ],
  },

  // ===== 出行者布局 =====
  {
    path: '/traveler',
    component: () => import('@/layouts/TravelerLayout.vue'),
    redirect: '/traveler/route-plan',
    children: [
      { path: 'route-plan', name: 'TravelerRoutePlan', component: () => import('@/views/traveler/RoutePlanView.vue'), meta: { title: '路径规划' } },
      { path: 'my-trips', name: 'TravelerMyTrips', component: () => import('@/views/traveler/MyTripsView.vue'), meta: { title: '我的行程', requiresAuth: true } },
      { path: 'alerts', name: 'TravelerAlerts', component: () => import('@/views/traveler/AlertsView.vue'), meta: { title: '出行提醒', requiresAuth: true } },
      { path: 'history', name: 'TravelerHistory', component: () => import('@/views/traveler/HistoryView.vue'), meta: { title: '历史记录', requiresAuth: true } },
      { path: 'account', name: 'TravelerAccount', component: () => import('@/views/traveler/AccountView.vue'), meta: { title: '账户设置', requiresAuth: true } },
    ],
  },

  // ===== 404 =====
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('@/views/NotFound.vue'), meta: { title: '404' } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} | 智能交通系统` : '智能交通系统'

  const token = localStorage.getItem('token')
  let role = ''
  if (token) role = getRoleFromToken(token)

  // ===== 登录/注册页 =====
  if (to.name === 'Login' || to.name === 'Register') {
    if (token && role && roleHomeMap[role]) return next(roleHomeMap[role])
    if (token && !role) {
      // 旧token无role → 允许重新登录获取新token
      return next()
    }
    return next()
  }

  // ===== 根路径重定向（按角色） =====
  if (to.path === '/') {
    if (!token) return next({ name: 'Login' })
    if (role && roleHomeMap[role]) return next(roleHomeMap[role])
    // 有token但无role → 要求重新登录
    useUserStore().logout()
    return next({ name: 'Login' })
  }

  // ===== 管理员路由守卫 =====
  if (to.path.startsWith('/admin')) {
    if (!token) return next({ name: 'Login', query: { redirect: to.fullPath } })
    if (role !== 'admin') return next({ name: 'Login' })
    return next()
  }

  // ===== 分析员路由守卫 =====
  if (to.path.startsWith('/analyst')) {
    if (!token) return next({ name: 'Login', query: { redirect: to.fullPath } })
    if (role !== 'analyst') return next({ name: 'Login' })
    return next()
  }

  // ===== 出行者路由守卫 =====
  if (to.path.startsWith('/traveler')) {
    if (to.meta.requiresAuth && !token) {
      return next({ name: 'Login', query: { redirect: to.fullPath } })
    }
    return next()
  }

  // ===== 旧版路由守卫（向后兼容） =====
  const userStore = useUserStore()
  if (to.meta.requiresAuth && !token) return next({ name: 'Login', query: { redirect: to.fullPath } })
  if (to.meta.role === 'admin' && role !== 'admin') return next({ name: 'Dashboard' })
  if ((to.name === 'Login' || to.name === 'Register') && token && role) {
    return next(roleHomeMap[role] || { name: 'Dashboard' })
  }
  next()
})

export default router
