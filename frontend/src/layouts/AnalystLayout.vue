<template>
  <el-container style="height: 100vh">
    <!-- 左侧侧边栏 280px -->
    <el-aside width="280px" class="analyst-aside">
      <div class="analyst-logo">
        <span class="analyst-logo-icon">🔬</span>
        <span class="analyst-logo-text">数据分析平台</span>
      </div>

      <!-- 模型训练状态指示灯 -->
      <div class="model-status-bar">
        <span class="status-label">模型状态</span>
        <span class="status-indicator" :class="modelStatusClass">
          <span class="status-dot" />
          <span class="status-text">{{ modelStatusText }}</span>
        </span>
      </div>

      <el-menu
        :default-active="route.path"
        router
        background-color="transparent"
        text-color="#8899aa"
        active-text-color="#00d4ff"
        class="analyst-menu"
      >
        <el-menu-item index="/analyst/models">🧠 模型管理</el-menu-item>
        <el-menu-item index="/analyst/propagation">🔬 拥堵传播</el-menu-item>
        <el-menu-item index="/analyst/carbon">🌿 碳排放</el-menu-item>
        <el-menu-item index="/analyst/explore">📊 数据探索</el-menu-item>
        <el-menu-item index="/analyst/scenarios">🔄 场景仿真</el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 右侧内容区 -->
    <el-container>
      <!-- 顶部栏 -->
      <el-header class="analyst-header">
        <div class="header-left">
          <span class="header-title">🔬 数据分析平台</span>
        </div>
        <div class="header-right">
          <span class="header-clock">{{ clockStr }}</span>
          <el-divider direction="vertical" />
          <el-tag size="small" type="warning" effect="dark" class="role-tag">分析员</el-tag>
          <span class="header-user">{{ userStore.userInfo?.username || '分析员' }}</span>
          <el-button text size="small" class="logout-btn" @click="handleLogout">退出</el-button>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="analyst-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

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

// 模型训练状态（默认待定，后续可由API/WebSocket更新）
const modelStatus = ref('idle') // idle | training | ready | error
const modelStatusMap = {
  idle: { class: 'status-idle', text: '待训练' },
  training: { class: 'status-training', text: '训练中...' },
  ready: { class: 'status-ready', text: '已就绪' },
  error: { class: 'status-error', text: '异常' },
}
const modelStatusClass = computed(() => `model-${modelStatus.value}`)
const modelStatusText = computed(() => modelStatusMap[modelStatus.value]?.text || '未知')

// 暴露更新方法供子组件使用
// 可通过 provide/inject 或 store 共享
window.__updateModelStatus = (status) => { modelStatus.value = status }

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.analyst-aside {
  background: var(--bg-panel);
  color: var(--text-primary);
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  overflow-y: auto;
}
.analyst-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.analyst-logo-icon { font-size: 28px; }
.analyst-logo-text {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
}

/* 模型状态栏 */
.model-status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 13px;
}
.status-label { color: var(--text-secondary); }
.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.status-text { font-size: 12px; }

/* 状态颜色 */
.model-idle .status-dot { background: #9e9e9e; }
.model-idle .status-text { color: #9e9e9e; }
.model-training .status-dot { background: #ffeb3b; box-shadow: 0 0 6px #ffeb3b; animation: pulse 1.5s infinite; }
.model-training .status-text { color: #ffeb3b; }
.model-ready .status-dot { background: #00e676; box-shadow: 0 0 6px #00e676; }
.model-ready .status-text { color: #00e676; }
.model-error .status-dot { background: #f44336; }
.model-error .status-text { color: #f44336; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.analyst-menu {
  flex: 1;
  border-right: none !important;
  padding: 8px 0;
}
.analyst-menu .el-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 24px !important;
  height: 48px;
  line-height: 48px;
  font-size: 14px;
}
.analyst-menu .el-menu-item:hover { background: rgba(255, 255, 255, 0.04); }
.analyst-menu .el-menu-item.is-active {
  background: rgba(0, 212, 255, 0.08);
  border-right: 3px solid var(--accent-blue);
}

.analyst-header {
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

.analyst-main {
  background: var(--bg-dark);
  padding: 20px;
  overflow-y: auto;
}
</style>
