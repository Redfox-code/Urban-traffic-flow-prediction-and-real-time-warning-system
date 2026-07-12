<template>
  <el-container style="height: 100vh">
    <!-- 左侧侧边栏 280px -->
    <el-aside width="280px" class="admin-aside">
      <div class="admin-logo">
        <span class="admin-logo-icon">🚥</span>
        <span class="admin-logo-text">智能交通管理平台</span>
      </div>
      <el-menu
        :default-active="route.path"
        router
        background-color="transparent"
        text-color="#8899aa"
        active-text-color="#00d4ff"
        class="admin-menu"
      >
        <el-menu-item index="/admin/dashboard">📊 实时监控</el-menu-item>
        <el-menu-item index="/admin/warnings">
          🚨 预警管理
          <el-badge
            v-if="warningStore.unreadCount > 0"
            :value="warningStore.unreadCount"
            class="admin-badge"
          />
        </el-menu-item>
        <el-menu-item index="/admin/signal-optimization">🚦 信号优化</el-menu-item>
        <el-menu-item index="/admin/emergency">🚑 应急调度</el-menu-item>
        <el-menu-item index="/admin/reports">📈 统计报表</el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 右侧内容区 -->
    <el-container>
      <!-- 顶部栏 -->
      <el-header class="admin-header">
        <div class="header-left">
          <span class="header-title">🚥 智能交通管理平台</span>
        </div>
        <div class="header-right">
          <span class="header-clock">{{ clockStr }}</span>
          <el-divider direction="vertical" />
          <el-tag size="small" type="danger" effect="dark" class="role-tag">管理员</el-tag>
          <span class="header-user">{{ userStore.userInfo?.username || '管理员' }}</span>
          <el-button text size="small" class="logout-btn" @click="handleLogout">退出</el-button>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { useWarningStore } from '@/store/warning'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const warningStore = useWarningStore()

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

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.admin-aside {
  background: var(--bg-panel);
  color: var(--text-primary);
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  overflow-y: auto;
}
.admin-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.admin-logo-icon { font-size: 28px; }
.admin-logo-text {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
}
.admin-menu {
  flex: 1;
  border-right: none !important;
  padding: 8px 0;
}
.admin-menu .el-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 24px !important;
  height: 48px;
  line-height: 48px;
  font-size: 14px;
}
.admin-menu .el-menu-item:hover { background: rgba(255, 255, 255, 0.04); }
.admin-menu .el-menu-item.is-active {
  background: rgba(0, 212, 255, 0.08);
  border-right: 3px solid var(--accent-blue);
}
.admin-badge { margin-left: auto; }
.admin-badge :deep(.el-badge__content) {
  background: #f44336;
  border: none;
  font-size: 11px;
  height: 18px;
  line-height: 18px;
  padding: 0 6px;
}

.admin-header {
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
.role-tag { font-size: 12px; }
.header-user { color: var(--text-primary); font-weight: 500; }
.logout-btn { color: var(--accent-blue); cursor: pointer; }

.admin-main {
  background: var(--bg-dark);
  padding: 20px;
  overflow-y: auto;
}
</style>
