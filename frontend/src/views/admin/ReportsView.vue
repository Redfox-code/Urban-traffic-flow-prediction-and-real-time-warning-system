<template>
  <div class="reports-view">
    <!-- 统计卡片行 -->
    <div class="report-cards">
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
          <div class="stat-value" style="color:#f44336">{{ dashData.today_warnings || 0 }}</div>
          <div class="stat-label">今日预警</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(255,152,0,.1)">📊</div>
        <div class="stat-body">
          <div class="stat-value" style="color:#ff9800">{{ dashData.avg_occupancy ?? '-' }}<small v-if="dashData.avg_occupancy != null">%</small></div>
          <div class="stat-label">平均占有率</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(76,175,80,.1)">⚡</div>
        <div class="stat-body">
          <div class="stat-value" style="color:#4caf50">{{ dashData.avg_efficiency_gain_pct || 0 }}<small>%</small></div>
          <div class="stat-label">信号效率提升</div>
        </div>
      </div>
    </div>

    <!-- 2x2 ECharts 图表网格 -->
    <div class="chart-grid">
      <el-card shadow="never" class="chart-card">
        <template #header>
          <span class="card-title">📈 24小时流量趋势</span>
          <el-tag v-if="loading" size="small" type="warning" effect="dark">加载中...</el-tag>
        </template>
        <div ref="trendChartRef" class="chart-container"></div>
      </el-card>

      <el-card shadow="never" class="chart-card">
        <template #header><span class="card-title">🥧 拥堵分布</span></template>
        <div ref="pieChartRef" class="chart-container"></div>
      </el-card>

      <el-card shadow="never" class="chart-card">
        <template #header><span class="card-title">📊 预警统计</span></template>
        <div ref="warnChartRef" class="chart-container"></div>
      </el-card>

      <el-card shadow="never" class="chart-card">
        <template #header><span class="card-title">📊 信号优化效果</span></template>
        <div ref="signalChartRef" class="chart-container"></div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { statsApi } from '@/api/stats'
import { warningApi } from '@/api/warning'

// ===== 状态 =====
const dashData = ref({})
const loading = ref(true)

// 图表 refs
const trendChartRef = ref(null)
const pieChartRef = ref(null)
const warnChartRef = ref(null)
const signalChartRef = ref(null)

// 图表实例
let trendChart = null
let pieChart = null
let warnChart = null
let signalChart = null

// 预警统计
const warnStats = ref({ info: 0, warning: 0, critical: 0 })

// ===== 暗色主题图表配色 =====
const colors = {
  blue: '#00d4ff',
  green: '#4caf50',
  red: '#f44336',
  orange: '#ff9800',
  indigo: '#2196f3',
}

// ===== 加载数据 =====
async function loadData() {
  loading.value = true
  try {
    const [statsRes, infoRes, warnRes, critRes] = await Promise.all([
      statsApi.getDashboard().catch(() => ({ data: { data: {} } })),
      warningApi.getList({ level: 'info', page: 1, page_size: 1 }).catch(() => ({ data: { data: { total: 0 } } })),
      warningApi.getList({ level: 'warning', page: 1, page_size: 1 }).catch(() => ({ data: { data: { total: 0 } } })),
      warningApi.getList({ level: 'critical', page: 1, page_size: 1 }).catch(() => ({ data: { data: { total: 0 } } })),
    ])

    dashData.value = statsRes.data?.data || statsRes.data || {}

    warnStats.value = {
      info: (infoRes.data?.data || infoRes.data || {}).total || 0,
      warning: (warnRes.data?.data || warnRes.data || {}).total || 0,
      critical: (critRes.data?.data || critRes.data || {}).total || 0,
    }

    await nextTick()
    renderAllCharts()
  } catch (e) {
    console.warn('报表数据加载失败', e)
  } finally {
    loading.value = false
  }
}

// ===== 渲染所有图表 =====
function renderAllCharts() {
  renderTrendChart()
  renderPieChart()
  renderWarnChart()
  renderSignalChart()
}

// ===== 1. 24小时流量趋势折线图 =====
function renderTrendChart() {
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
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
    },
    legend: {
      data: ['平均占有率', '平均速度'],
      textStyle: { color: '#8899aa', fontSize: 11 },
      top: 0,
    },
    grid: { left: 50, right: 50, top: 36, bottom: 24 },
    xAxis: {
      type: 'category',
      data: hours,
      axisLabel: { color: '#8899aa', fontSize: 10, interval: 3 },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,.08)' } },
    },
    yAxis: [
      {
        type: 'value',
        name: '占有率(%)',
        nameTextStyle: { color: '#8899aa', fontSize: 10 },
        axisLabel: { color: '#8899aa', fontSize: 10 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,.04)' } },
      },
      {
        type: 'value',
        name: '速度(km/h)',
        nameTextStyle: { color: '#8899aa', fontSize: 10 },
        axisLabel: { color: '#8899aa', fontSize: 10 },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '平均占有率',
        type: 'line',
        data: occData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { color: colors.red, width: 2 },
        itemStyle: { color: colors.red },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(244,67,54,.15)' },
            { offset: 1, color: 'rgba(244,67,54,0)' },
          ]),
        },
        connectNulls: true,
      },
      {
        name: '平均速度',
        type: 'line',
        yAxisIndex: 1,
        data: spdData,
        smooth: true,
        symbol: 'diamond',
        symbolSize: 4,
        lineStyle: { color: colors.blue, width: 2 },
        itemStyle: { color: colors.blue },
        connectNulls: true,
      },
    ],
  })
}

// ===== 2. 拥堵分布饼图 =====
function renderPieChart() {
  if (!pieChartRef.value) return
  if (pieChart) pieChart.dispose()
  pieChart = echarts.init(pieChartRef.value)

  pieChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}% ({d}%)',
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: { color: '#8899aa', fontSize: 11 },
    },
    series: [
      {
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['40%', '50%'],
        avoidLabelOverlap: false,
        label: {
          show: false,
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold',
            color: '#e0e6ed',
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0,0,0,.5)',
          },
        },
        labelLine: { show: false },
        data: [
          { value: 30, name: '畅通', itemStyle: { color: colors.green } },
          { value: 35, name: '缓行', itemStyle: { color: colors.orange } },
          { value: 25, name: '拥堵', itemStyle: { color: colors.red } },
          { value: 10, name: '严重', itemStyle: { color: '#b71c1c' } },
        ],
      },
    ],
  })
}

// ===== 3. 预警统计柱状图 =====
function renderWarnChart() {
  if (!warnChartRef.value) return
  if (warnChart) warnChart.dispose()
  warnChart = echarts.init(warnChartRef.value)

  warnChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    grid: { left: 45, right: 20, top: 20, bottom: 30 },
    xAxis: {
      type: 'category',
      data: ['提示(info)', '警告(warning)', '严重(critical)'],
      axisLabel: { color: '#8899aa', fontSize: 11 },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,.08)' } },
    },
    yAxis: {
      type: 'value',
      name: '数量',
      nameTextStyle: { color: '#8899aa', fontSize: 10 },
      axisLabel: { color: '#8899aa', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,.04)' } },
    },
    series: [
      {
        type: 'bar',
        barWidth: '50%',
        data: [
          { value: warnStats.value.info, itemStyle: { color: colors.indigo } },
          { value: warnStats.value.warning, itemStyle: { color: colors.orange } },
          { value: warnStats.value.critical, itemStyle: { color: colors.red } },
        ],
      },
    ],
  })
}

// ===== 4. 信号优化效果柱状图 =====
function renderSignalChart() {
  if (!signalChartRef.value) return
  if (signalChart) signalChart.dispose()
  signalChart = echarts.init(signalChartRef.value)

  const total = dashData.value.signal_optimizations_total || 0
  const applied = dashData.value.signal_optimizations_applied || 0
  const pending = total - applied

  signalChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const p = params[0]
        return `${p.name}: ${p.value}次`
      },
    },
    grid: { left: 45, right: 20, top: 20, bottom: 30 },
    xAxis: {
      type: 'category',
      data: ['已应用', '待应用'],
      axisLabel: { color: '#8899aa', fontSize: 11 },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,.08)' } },
    },
    yAxis: {
      type: 'value',
      name: '次数',
      nameTextStyle: { color: '#8899aa', fontSize: 10 },
      axisLabel: { color: '#8899aa', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,.04)' } },
    },
    series: [
      {
        type: 'bar',
        barWidth: '40%',
        data: [
          { value: applied, itemStyle: { color: colors.green } },
          { value: Math.max(0, pending), itemStyle: { color: colors.blue } },
        ],
      },
    ],
  })
}

// ===== 窗口 Resize =====
function handleResize() {
  trendChart?.resize()
  pieChart?.resize()
  warnChart?.resize()
  signalChart?.resize()
}

// ===== 生命周期 =====
onMounted(async () => {
  await loadData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  pieChart?.dispose()
  warnChart?.dispose()
  signalChart?.dispose()
})
</script>

<style scoped>
.reports-view {
  max-width: 1400px;
}

/* 统计卡片 */
.report-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  background: var(--bg-panel);
  border: 1px solid rgba(255,255,255,.06);
  border-radius: 10px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 14px;
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-value small {
  font-size: 13px;
  font-weight: 400;
  color: var(--text-secondary);
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

/* 图表网格 */
.chart-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

@media (max-width: 960px) {
  .chart-grid { grid-template-columns: 1fr; }
}

.chart-card {
  background: var(--bg-panel);
}

.card-title {
  font-weight: 600;
  color: var(--text-primary);
}

.chart-container {
  width: 100%;
  height: 280px;
}
</style>
