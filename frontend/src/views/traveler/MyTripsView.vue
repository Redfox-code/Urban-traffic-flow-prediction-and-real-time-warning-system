<template>
  <div class="my-trips-view">
    <div class="mtv-header">
      <h2>👤 我的行程</h2>
      <el-button v-if="profiles.length > 0" text size="small" @click="refreshProfile" :loading="loading">
        🔄 刷新
      </el-button>
    </div>

    <!-- 加载体 -->
    <div v-if="loading && profiles.length === 0" class="mtv-loading">
      <el-skeleton :rows="3" animated />
    </div>

    <!-- 空状态 -->
    <el-empty v-else-if="profiles.length === 0 && !loading"
      description="还没有常用路线">
      <template #image>
        <div class="mtv-empty-icon">🗺️</div>
      </template>
      <p style="color:var(--text-secondary);font-size:13px">
        去规划您的第一条路线吧
      </p>
      <el-button type="primary" @click="goRoutePlan">🚘 去规划路线</el-button>
    </el-empty>

    <!-- 上限提示 -->
    <div v-if="profiles.length >= 3" class="mtv-limit-hint">
      ⚠️ 最多保存3条行程（已达上限），保存新路线将自动替换最旧记录
    </div>

    <!-- 卡片网格 -->
    <template v-else>
      <div class="mtv-grid">
        <div v-for="p in profiles" :key="p.id" class="mtv-card" @click="goRouteWith(p)">
          <!-- 卡片头部 -->
          <div class="mtv-card-header">
            <div class="mtv-card-icon">
              {{ getRouteIcon(p) }}
            </div>
            <div class="mtv-card-meta">
              <div class="mtv-card-title">{{ p.route_label || '常用路线' }}</div>
              <div class="mtv-card-subtitle">{{ p.origin_name }} → {{ p.dest_name }}</div>
            </div>
            <el-tag v-if="p.frequency >= 3" size="small" type="warning" effect="dark" class="mtv-tag-freq">
              常走
            </el-tag>
          </div>

          <!-- 时段+频率 -->
          <div class="mtv-card-info">
            <span v-if="p.depart_hour_avg != null" class="mtv-info-item">
              🕐 {{ formatHour(p.depart_hour_avg) }}
            </span>
            <span class="mtv-info-item">
              📊 {{ p.frequency }} 次
            </span>
            <span v-if="p.last_used_at" class="mtv-info-item">
              📅 {{ formatDate(p.last_used_at) }}
            </span>
          </div>

          <!-- 路况指示条 -->
          <div class="mtv-traffic-bar">
            <div class="mtv-bar-track">
              <div class="mtv-bar-fill" :style="{ width: trafficPercent(p) + '%', background: trafficColor(p) }"></div>
            </div>
            <span class="mtv-traffic-label">{{ trafficLabel(p) }}</span>
          </div>

          <!-- 标签 + 提醒开关 -->
          <div class="mtv-card-tags">
            <el-tag v-if="p.alert_enabled" size="small" type="success" effect="plain" @click.stop="toggleAlert(p)" style="cursor:pointer">🔔 提醒已开</el-tag>
            <el-tag v-else size="small" type="info" effect="plain" @click.stop="toggleAlert(p)" style="cursor:pointer">🔕 提醒关闭</el-tag>
          </div>

          <!-- 删除按钮 -->
          <el-button class="mtv-delete-btn" text size="small" type="danger" @click.stop="deleteTrip(p)">
            ✕ 删除
          </el-button>
        </div>
      </div>

      <!-- 出行时段分布图 -->
      <el-card shadow="never" class="mtv-chart-card">
        <template #header>
          <span style="font-weight:bold;color:var(--text-primary)">📊 出行时段分布</span>
        </template>
        <div ref="chartRef" class="mtv-chart"></div>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store/user'
import { travelerApi } from '@/api/traveler'
import { trafficApi } from '@/api/traffic'
import * as echarts from 'echarts'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const profiles = ref([])
const loading = ref(true)
const chartRef = ref(null)
let chartInstance = null
let trafficTimer = null

// ===== 加载数据 =====
async function refreshProfile() {
  loading.value = true
  try {
    const res = await travelerApi.getProfile()
    profiles.value = res.data?.profiles || res?.profiles || []
  } catch (e) {
    console.warn('加载画像失败', e)
    if (profiles.value.length === 0) profiles.value = []
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await refreshProfile()
  nextTick(initChart)
  // 30s轮询路况
  trafficTimer = setInterval(refreshTraffic, 30000)
})

onUnmounted(() => {
  if (trafficTimer) clearInterval(trafficTimer)
  if (chartInstance) { chartInstance.dispose(); chartInstance = null }
})

// 监听路由，导航到本页时自动刷新
watch(() => route.name, (n) => { if (n === 'TravelerMyTrips') refreshProfile() })

// ===== 路况刷新 =====
const trafficMap = ref({})
async function refreshTraffic() {
  try {
    const res = await trafficApi.getCurrent()
    const items = res.data?.items || res?.items || []
    const map = {}
    items.forEach(item => { map[item.section_id] = item })
    trafficMap.value = map
  } catch { /* silent */ }
}

// ===== 卡片属性 =====
function getRouteIcon(p) {
  const h = p.depart_hour_avg
  if (h == null) return '🚗'
  if (h >= 5 && h < 9) return '🌅'
  if (h >= 9 && h < 12) return '☀️'
  if (h >= 12 && h < 14) return '🍽️'
  if (h >= 14 && h < 18) return '🌤️'
  if (h >= 18 && h < 22) return '🌆'
  return '🌙'
}

function formatHour(h) {
  if (h == null) return ''
  const hour = Math.floor(h)
  const min = Math.round((h - hour) * 60)
  return `${String(hour).padStart(2, '0')}:${String(min).padStart(2, '0')}`
}

function formatDate(iso) {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    return `${d.getMonth() + 1}/${d.getDate()}`
  } catch { return iso?.slice(5, 10) || '' }
}

// ===== 路况指示条 =====
function trafficPercent(p) {
  const t = trafficMap.value[p.id]
  if (!t) return 50
  const occ = t.occupancy || 50
  return Math.min(occ, 100)
}
function trafficColor(p) {
  const t = trafficMap.value[p.id]
  if (!t) return 'var(--traffic-slow)'
  const occ = t.occupancy || 50
  if (occ < 30) return 'var(--traffic-smooth)'
  if (occ < 60) return 'var(--traffic-slow)'
  if (occ < 85) return 'var(--traffic-congested)'
  return 'var(--traffic-jammed)'
}
function trafficLabel(p) {
  const t = trafficMap.value[p.id]
  if (!t) return '暂无数据'
  const occ = t.occupancy || 0
  if (occ < 30) return '🟢 畅通'
  if (occ < 60) return '🟡 缓行'
  if (occ < 85) return '🟠 拥堵'
  return '🔴 严重'
}

// ===== ECharts 出行时段分布 =====
function initChart() {
  if (!chartRef.value || profiles.value.length === 0) return
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(chartRef.value)

  // 按小时统计
  const hours = Array.from({ length: 24 }, (_, i) => i)
  const counts = hours.map(h => {
    return profiles.value.filter(p => {
      if (p.depart_hour_avg == null) return false
      return Math.floor(p.depart_hour_avg) === h
    }).length
  })

  chartInstance.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 16, top: 10, bottom: 30 },
    xAxis: {
      type: 'category',
      data: hours.map(h => `${String(h).padStart(2, '0')}:00`),
      axisLabel: { color: '#8899aa', fontSize: 11, interval: 3 },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,.08)' } },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: '#8899aa', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,.04)' } },
    },
    series: [{
      type: 'bar',
      data: counts,
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#00d4ff' },
          { offset: 1, color: '#0066ff' },
        ]),
        borderRadius: [4, 4, 0, 0],
      },
      emphasis: { itemStyle: { color: '#00d4ff' } },
      barMaxWidth: 20,
    }],
  })

  chartInstance.on('click', (params) => {
    const hour = params.dataIndex
    const matched = profiles.value.filter(p => {
      if (p.depart_hour_avg == null) return false
      return Math.floor(p.depart_hour_avg) === hour
    })
    if (matched.length > 0) {
      // 跳转第一个匹配的路线的路径规划
      goRouteWith(matched[0])
    }
  })
}

// ===== 导航 =====
function goRoutePlan() {
  router.push({ name: 'TravelerRoutePlan' })
}

function goRouteWith(p) {
  router.push({
    name: 'TravelerRoutePlan',
    query: {
      origin_name: p.origin_name,
      origin_lat: p.origin_lat,
      origin_lng: p.origin_lng,
      dest_name: p.dest_name,
      dest_lat: p.dest_lat,
      dest_lng: p.dest_lng,
    }
  })
}

// ===== 删除行程 =====
async function deleteTrip(p) {
  try {
    await ElMessageBox.confirm(`确认删除"${p.route_label || p.origin_name + '→' + p.dest_name}"？`, '删除行程', {
      confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning'
    })
  } catch { return }
  try {
    await travelerApi.deleteRoute(p.id)
    ElMessage.success('已删除')
    refreshProfile()
    nextTick(initChart)
  } catch { ElMessage.error('删除失败') }
}

async function toggleAlert(p) {
  const newState = !p.alert_enabled
  try {
    await travelerApi.updateAlertSettings({ profile_id: p.id, alert_enabled: newState })
    p.alert_enabled = newState
    ElMessage.success(newState ? '已开启提醒' : '已关闭提醒')
  } catch { ElMessage.error('操作失败') }
}
</script>

<style scoped>
.my-trips-view {
  max-width: 900px;
  margin: 0 auto;
}
.mtv-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.mtv-header h2 {
  color: var(--text-primary);
  font-size: 20px;
  margin: 0;
}
.mtv-loading {
  padding: 40px 20px;
}
.mtv-empty-icon {
  font-size: 60px;
  text-align: center;
  line-height: 1;
}
/* 卡片网格 */
.mtv-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}
@media (max-width: 640px) {
  .mtv-grid {
    grid-template-columns: 1fr;
  }
}
.mtv-card {
  background: var(--bg-panel);
  border: 1px solid rgba(255,255,255,.06);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: border-color .2s, transform .15s;
}
.mtv-card:hover {
  border-color: var(--accent-blue);
  transform: translateY(-2px);
}
.mtv-card:active {
  transform: translateY(0);
}
.mtv-card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}
.mtv-card-icon {
  width: 40px;
  height: 40px;
  background: rgba(0,212,255,.1);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}
.mtv-card-meta {
  flex: 1;
  min-width: 0;
}
.mtv-card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.mtv-card-subtitle {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.mtv-tag-freq {
  flex-shrink: 0;
}
.mtv-card-info {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}
.mtv-info-item {
  font-size: 12px;
  color: var(--text-secondary);
}
/* 路况指示条 */
.mtv-traffic-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.mtv-bar-track {
  flex: 1;
  height: 6px;
  background: rgba(255,255,255,.08);
  border-radius: 3px;
  overflow: hidden;
}
.mtv-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s, background 0.5s;
}
.mtv-traffic-label {
  font-size: 11px;
  color: var(--text-secondary);
  white-space: nowrap;
}
.mtv-card-tags {
  display: flex;
  gap: 6px;
}
.mtv-delete-btn {
  margin-top: 8px; width: 100%; justify-content: center;
  opacity: 0; transition: opacity .2s;
}
.mtv-card:hover .mtv-delete-btn { opacity: 1; }
.mtv-limit-hint {
  font-size: 12px; color: #ff9800; background: rgba(255,152,0,.08);
  border-radius: 6px; padding: 8px 12px; margin-bottom: 12px; text-align: center;
}
/* 图表 */
.mtv-chart-card {
  margin-top: 8px;
}
.mtv-chart {
  width: 100%;
  height: 200px;
}
</style>
