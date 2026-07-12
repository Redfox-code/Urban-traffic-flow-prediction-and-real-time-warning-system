<template>
  <div class="dashboard-view">
    <!-- 统计卡片行 -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(0,212,255,.1)">🛣️</div>
        <div class="stat-body">
          <div class="stat-value">{{ dashData.total_sections || 0 }}</div>
          <div class="stat-label">路段总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(244,67,54,.1)">🚨</div>
        <div class="stat-body">
          <div class="stat-value" style="color:#f44336">{{ dashData.active_warnings || 0 }}</div>
          <div class="stat-label">活跃预警</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(255,152,0,.1)">🚑</div>
        <div class="stat-body">
          <div class="stat-value" style="color:#ff9800">{{ dashData.active_emergencies || 0 }}</div>
          <div class="stat-label">活跃应急</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(76,175,80,.1)">🚦</div>
        <div class="stat-body">
          <div class="stat-value" style="color:#4caf50">{{ dashData.signal_optimizations_applied || 0 }}</div>
          <div class="stat-label">信号优化(已应用)</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(156,39,176,.1)">📊</div>
        <div class="stat-body">
          <div class="stat-value">{{ dashData.avg_occupancy ?? '-' }}<small v-if="dashData.avg_occupancy != null">%</small></div>
          <div class="stat-label">平均占有率</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(33,150,243,.1)">⚡</div>
        <div class="stat-body">
          <div class="stat-value" style="color:#2196f3">{{ dashData.avg_efficiency_gain_pct || 0 }}<small>%</small></div>
          <div class="stat-label">平均效率提升</div>
        </div>
      </div>
    </div>

    <!-- 图表 + 表格双列 -->
    <div class="dash-grid">
      <el-card shadow="never" class="dash-card">
        <template #header>
          <span class="card-title">📈 24小时路况趋势</span>
          <el-tag v-if="loading" size="small" type="warning" effect="dark">更新中...</el-tag>
        </template>
        <div ref="trendChartRef" class="dash-chart"></div>
      </el-card>

      <el-card shadow="never" class="dash-card">
        <template #header>
          <span class="card-title">🔥 实时路况 TOP10</span>
          <el-button text size="small" @click="refreshAll" :loading="loading">🔄 刷新</el-button>
        </template>
        <el-table :data="topSections" size="small" style="width:100%" max-height="320" v-loading="loading">
          <el-table-column prop="section_name" label="路段" min-width="120" show-overflow-tooltip />
          <el-table-column prop="occupancy" label="占有率" width="80" sortable>
            <template #default="{row}">{{ row.occupancy }}%</template>
          </el-table-column>
          <el-table-column prop="avg_speed" label="速度" width="70" sortable>
            <template #default="{row}">{{ row.avg_speed }} km/h</template>
          </el-table-column>
          <el-table-column prop="level" label="状态" width="80">
            <template #default="{row}">
              <el-tag size="small" :type="levelType(row.level)" effect="dark">
                {{ levelLabel(row.level) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 底部：今日预警 + 信号优化 -->
    <div class="dash-grid">
      <el-card shadow="never" class="dash-card">
        <template #header>
          <span class="card-title">🚨 今日预警 ({{ dashData.today_warnings || 0 }})</span>
          <span v-if="dashData.today_critical > 0" class="critical-badge">🔴 严重 {{ dashData.today_critical }}</span>
        </template>
        <el-empty v-if="recentWarnings.length === 0" description="暂无预警" :image-size="60" />
        <div v-else class="warning-list">
          <div v-for="w in recentWarnings" :key="w.id" class="warning-item">
            <el-tag size="small" :type="w.level === 'critical' ? 'danger' : w.level === 'warning' ? 'warning' : 'info'" effect="dark">
              {{ w.level }}
            </el-tag>
            <span class="warning-msg">{{ w.message }}</span>
            <span class="warning-time">{{ formatTime(w.created_at) }}</span>
          </div>
        </div>
      </el-card>

      <el-card shadow="never" class="dash-card">
        <template #header>
          <span class="card-title">🚦 信号优化效果 (累计 {{ dashData.signal_optimizations_total || 0 }} 次)</span>
        </template>
        <el-empty v-if="(dashData.signal_optimizations_total || 0) === 0" description="暂无优化记录" :image-size="60" />
        <div v-else class="signal-summary">
          <div class="signal-stat">
            <div class="signal-stat-num" style="color:#4caf50">{{ dashData.signal_optimizations_applied || 0 }}</div>
            <div class="signal-stat-label">已应用</div>
          </div>
          <div class="signal-stat">
            <div class="signal-stat-num" style="color:#2196f3">{{ dashData.signal_optimizations_total || 0 }}</div>
            <div class="signal-stat-label">总优化</div>
          </div>
          <div class="signal-stat">
            <div class="signal-stat-num" style="color:#ff9800">{{ dashData.avg_efficiency_gain_pct || 0 }}%</div>
            <div class="signal-stat-label">平均效率提升</div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { statsApi } from '@/api/stats'
import { trafficApi } from '@/api/traffic'
import { warningApi } from '@/api/warning'
import * as echarts from 'echarts'

const dashData = ref({})
const topSections = ref([])
const recentWarnings = ref([])
const loading = ref(true)
const trendChartRef = ref(null)
let trendChart = null
let refreshTimer = null

async function refreshAll() {
  loading.value = true
  try {
    const [statsRes, trafficRes, warnRes] = await Promise.all([
      statsApi.getDashboard().catch(() => ({ data: { data: {} } })),
      trafficApi.getCurrent().catch(() => ({ data: { data: [] } })),
      warningApi.getList({ page: 1, page_size: 5, is_resolved: 'false' }).catch(() => ({ data: { data: { items: [] } } })),
    ])
    dashData.value = statsRes.data?.data || statsRes.data || {}
    const items = trafficRes.data?.data || trafficRes.data || []
    if (Array.isArray(items)) {
      topSections.value = [...items].sort((a, b) => (b.occupancy || 0) - (a.occupancy || 0)).slice(0, 10)
    }
    const warnData = warnRes.data?.data || warnRes.data || {}
    recentWarnings.value = (warnData.items || []).slice(0, 5)
    await nextTick()
    renderChart()
  } catch (e) {
    console.warn('Dashboard刷新失败', e)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await refreshAll()
  refreshTimer = setInterval(refreshAll, 30000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  if (trendChart) { trendChart.dispose(); trendChart = null }
})

function renderChart() {
  if (!trendChartRef.value) return
  if (trendChart) trendChart.dispose()
  trendChart = echarts.init(trendChartRef.value)
  const trend = dashData.value.traffic_trend || []
  const hours = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`)
  const occData = Array(24).fill(null)
  const spdData = Array(24).fill(null)
  trend.forEach(t => {
    const idx = t.hour
    if (idx >= 0 && idx < 24) {
      occData[idx] = t.avg_occupancy
      spdData[idx] = t.avg_speed
    }
  })
  trendChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    legend: { data: ['平均占有率', '平均速度'], textStyle: { color: '#8899aa', fontSize: 11 }, top: 0 },
    grid: { left: 50, right: 50, top: 36, bottom: 24 },
    xAxis: {
      type: 'category', data: hours,
      axisLabel: { color: '#8899aa', fontSize: 10, interval: 3 },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,.08)' } },
    },
    yAxis: [
      {
        type: 'value', name: '占有率(%)',
        nameTextStyle: { color: '#8899aa', fontSize: 10 },
        axisLabel: { color: '#8899aa', fontSize: 10 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,.04)' } },
      },
      {
        type: 'value', name: '速度(km/h)',
        nameTextStyle: { color: '#8899aa', fontSize: 10 },
        axisLabel: { color: '#8899aa', fontSize: 10 },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '平均占有率', type: 'line', data: occData, smooth: true,
        symbol: 'circle', symbolSize: 4,
        lineStyle: { color: '#f44336', width: 2 }, itemStyle: { color: '#f44336' },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(244,67,54,.15)' }, { offset: 1, color: 'rgba(244,67,54,0)' }]) },
        connectNulls: true,
      },
      {
        name: '平均速度', type: 'line', yAxisIndex: 1, data: spdData, smooth: true,
        symbol: 'diamond', symbolSize: 4,
        lineStyle: { color: '#00d4ff', width: 2 }, itemStyle: { color: '#00d4ff' },
        connectNulls: true,
      },
    ],
  })
}

function levelType(level) {
  const map = { smooth: 'success', slow: 'warning', congested: 'danger', jammed: 'danger' }
  return map[level] || 'info'
}
function levelLabel(level) {
  const map = { smooth: '畅通', slow: '缓行', congested: '拥堵', jammed: '严重' }
  return map[level] || level
}
function formatTime(iso) {
  if (!iso) return ''
  try { return iso.slice(11, 19) } catch { return iso }
}
</script>

<style scoped>
.dashboard-view { max-width: 1400px; }
.stat-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin-bottom: 16px; }
.stat-card { background: var(--bg-panel); border: 1px solid rgba(255,255,255,.06); border-radius: 10px; padding: 16px; display: flex; align-items: center; gap: 14px; }
.stat-icon { width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0; }
.stat-value { font-size: 24px; font-weight: 700; color: var(--text-primary); line-height: 1.2; }
.stat-value small { font-size: 13px; font-weight: 400; color: var(--text-secondary); }
.stat-label { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }
.dash-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }
@media (max-width: 960px) { .dash-grid { grid-template-columns: 1fr; } }
.dash-card { background: var(--bg-panel); }
.card-title { font-weight: 600; color: var(--text-primary); }
.dash-chart { width: 100%; height: 280px; }
.warning-list { display: flex; flex-direction: column; gap: 8px; }
.warning-item { display: flex; align-items: center; gap: 8px; padding: 8px 10px; background: rgba(255,255,255,.02); border-radius: 6px; font-size: 13px; }
.warning-msg { flex: 1; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.warning-time { color: var(--text-secondary); font-size: 11px; white-space: nowrap; }
.critical-badge { font-size: 12px; color: #f44336; font-weight: 600; }
.signal-summary { display: flex; gap: 24px; justify-content: center; padding: 16px 0; }
.signal-stat { text-align: center; }
.signal-stat-num { font-size: 28px; font-weight: 700; }
.signal-stat-label { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }
</style>
