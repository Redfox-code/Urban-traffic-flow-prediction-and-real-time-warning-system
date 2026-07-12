<template>
  <el-container style="height: 100vh">
    <!-- ≥768px: 左侧侧边栏 -->
    <el-aside v-if="!isMobile" width="280px" class="traveler-aside">
      <div class="traveler-logo">
        <span class="traveler-logo-icon">🗺️</span>
        <span class="traveler-logo-text">智能出行助手</span>
      </div>
      <el-menu
        :default-active="route.path"
        router
        background-color="transparent"
        text-color="#8899aa"
        active-text-color="#00d4ff"
        class="traveler-menu"
      >
        <el-menu-item index="/traveler/route-plan" @click="handleNavClick('route-plan')">
          <span>🏠 路径规划</span>
        </el-menu-item>
        <el-menu-item index="/traveler/alerts" @click="handleNavClick('alerts')">
          <span>🔔 出行提醒</span>
        </el-menu-item>
        <el-menu-item index="/traveler/my-trips" @click="handleNavClick('my-trips')">
          <span>👤 我的行程</span>
        </el-menu-item>
        <el-menu-item index="/traveler/account" @click="handleNavClick('account')">
          <span>⚙️ 账户设置</span>
        </el-menu-item>
      </el-menu>

      <!-- 底部用户信息 -->
      <div class="traveler-sidebar-footer">
        <template v-if="userStore.isLoggedIn">
          <div class="sidebar-user">
            <el-avatar size="small" style="background: var(--accent-blue); vertical-align: middle;">
              {{ (userStore.userInfo?.username || 'U')[0].toUpperCase() }}
            </el-avatar>
            <span class="sidebar-username">{{ userStore.userInfo?.username || '用户' }}</span>
          </div>
          <el-button text size="small" class="logout-btn" @click="handleLogout">退出</el-button>
        </template>
        <template v-else>
          <el-button type="primary" size="small" class="login-btn" @click="goLogin">登录 / 注册</el-button>
        </template>
      </div>
    </el-aside>

    <!-- 右侧内容区 -->
    <el-container>
      <!-- 顶部栏（仅 ≥768px 显示，带标题） -->
      <el-header v-if="!isMobile" class="traveler-header">
        <div class="header-left">
          <span class="header-title">🗺️ 智能出行助手</span>
        </div>
        <div class="header-right">
          <span class="header-clock">{{ clockStr }}</span>
          <el-divider direction="vertical" />
          <span class="header-user">{{ userStore.userInfo?.username || '出行者' }}</span>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="traveler-main">
        <router-view />
      </el-main>
    </el-container>

    <!-- <768px: 底部Tab栏 -->
    <div v-if="isMobile" class="mobile-tab-bar">
      <div
        v-for="tab in tabs"
        :key="tab.path"
        class="mobile-tab-item"
        :class="{ active: route.path === tab.path }"
        @click="handleNavClick(tab.key)"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
      </div>
    </div>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 响应式检测
const isMobile = ref(window.innerWidth < 768)
function checkMobile() { isMobile.value = window.innerWidth < 768 }
window.addEventListener('resize', checkMobile)
onBeforeUnmount(() => window.removeEventListener('resize', checkMobile))

// 实时时钟
const clockStr = ref('')
let clockTimer = null
function updateClock() {
  const now = new Date()
  clockStr.value = now.toLocaleString('zh-CN', { hour12: false })
}
updateClock()
onMounted(() => { clockTimer = setInterval(updateClock, 1000) })
onUnmounted(() => { if (clockTimer) clearInterval(clockTimer) })

// Tab定义
const tabs = [
  { path: '/traveler/route-plan', key: 'route-plan', icon: '🏠', label: '规划' },
  { path: '/traveler/alerts', key: 'alerts', icon: '🔔', label: '提醒' },
  { path: '/traveler/my-trips', key: 'my-trips', icon: '👤', label: '我的' },
  { path: '/traveler/account', key: 'account', icon: '⚙️', label: '账户' },
]

// 需要登录的tab
const authRequiredTabs = ['alerts', 'my-trips', 'account']

function handleNavClick(key) {
  if (authRequiredTabs.includes(key) && !userStore.isLoggedIn) {
    // 未登录 → 弹出登录引导
    ElMessageBox.confirm('此功能需要登录，是否前往登录？', '提示', {
      confirmButtonText: '去登录',
      cancelButtonText: '取消',
      type: 'info',
    }).then(() => {
      router.push({ name: 'Login', query: { redirect: route.fullPath } })
    }).catch(() => {
      // 取消
    })
    return
  }
  // 已登录或公开路径 → 直接跳转
  const target = tabs.find(t => t.key === key)
  if (target) router.push(target.path)
}

function goLogin() {
  router.push({ name: 'Login' })
}

function handleLogout() {
  userStore.logout()
  router.push('/traveler/route-plan')
}
</script>

<style scoped>
.traveler-aside {
  background: var(--bg-panel);
  color: var(--text-primary);
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  overflow-y: auto;
}
.traveler-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.traveler-logo-icon { font-size: 28px; }
.traveler-logo-text {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
}
.traveler-menu {
  flex: 1;
  border-right: none !important;
  padding: 8px 0;
}
.traveler-menu .el-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 24px !important;
  height: 48px;
  line-height: 48px;
  font-size: 14px;
}
.traveler-menu .el-menu-item:hover { background: rgba(255, 255, 255, 0.04); }
.traveler-menu .el-menu-item.is-active {
  background: rgba(0, 212, 255, 0.08);
  border-right: 3px solid var(--accent-blue);
}

.traveler-sidebar-footer {
  padding: 16px 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.sidebar-user { display: flex; align-items: center; gap: 8px; }
.sidebar-username { font-size: 13px; color: var(--text-primary); }
.login-btn { width: 100%; }
.logout-btn { color: var(--accent-blue); }

/* Header */
.traveler-header {
  background: var(--bg-panel);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  height: 60px !important;
  padding: 0 24px;
}
.header-left { display: flex; align-items: center; }
.header-title { font-size: 16px; font-weight: 600; }
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: var(--text-secondary);
}
.header-clock { font-variant-numeric: tabular-nums; }
.header-user { color: var(--text-primary); font-weight: 500; }

/* Main */
.traveler-main {
  background: var(--bg-dark);
  padding: 20px;
  overflow-y: auto;
  padding-bottom: 70px; /* 给底部Tab留空间（移动端） */
}

/* ===== 移动端底部Tab栏 ===== */
.mobile-tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: var(--bg-panel);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-around;
  z-index: 1000;
  padding-bottom: env(safe-area-inset-bottom, 0);
}
.mobile-tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding: 6px 12px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: color 0.2s;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}
.mobile-tab-item.active { color: var(--accent-blue); }
.mobile-tab-item:active { opacity: 0.7; }
.tab-icon { font-size: 22px; line-height: 1; }
.tab-label { font-size: 11px; white-space: nowrap; }
</style>
