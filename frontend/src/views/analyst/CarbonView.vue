<template>
  <div class="carbon-view">
    <div class="page-header">
      <h2>碳排放监测</h2>
      <el-radio-group v-model="period" size="small" @change="loadData">
        <el-radio-button value="day">日</el-radio-button>
        <el-radio-button value="week">周</el-radio-button>
        <el-radio-button value="month">月</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 概览统计 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ summary.total_co2_kg }}</div>
          <div class="stat-label">总排放 (kg/h)</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value extra">{{ summary.total_extra_co2_kg }}</div>
          <div class="stat-label">拥堵额外排放 (kg/h)</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ summary.sections_count }}</div>
          <div class="stat-label">监测路段数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ summary.avg_speed }}</div>
          <div class="stat-label">平均速度 (km/h)</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <!-- 全城排放趋势 -->
      <el-col :span="14">
        <el-card class="chart-card" v-loading="loadingTrend">
          <template #header>{{ periodText }}排放趋势</template>
          <div ref="trendChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <!-- 拥堵额外排放堆叠 -->
      <el-col :span="10">
        <el-card class="chart-card" v-loading="loadingTrend">
          <template #header>{{ periodText }}排放构成</template>
          <div ref="stackedChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 路段排放Top10 -->
    <el-card class="chart-card top-card" v-loading="loadingTop">
      <template #header>路段碳排放 Top10</template>
      <div ref="topChartRef" class="chart-container top-chart"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { carbonApi } from '@/api/carbon'
import * as echarts from 'echarts/core'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent, CanvasRenderer])

const period = ref('day')
const loadingTrend = ref(false)
const loadingTop = ref(false)
const trendData = ref([])
const topData = ref([])
const summary = ref({ total_co2_kg: '--', total_extra_co2_kg: '--', sections_count: '--', avg_speed: '--' })

const trendChartRef = ref(null)
const stackedChartRef = ref(null)
const topChartRef = ref(null)
let trendChart = null, stackedChart = null, topChart = null

const periodText = computed(() => ({ day: '逐时', week: '逐日', month: '逐日' })[period.value] || '')

async function loadData() {
  loadingTrend.value = true
  try {
    const res = await carbonApi.getTrend(period.value)
    const data = res.data || res
    trendData.value = data.items || data || []
    // summary from first data point or separate endpoint
    if (trendData.value.length > 0) {
      const last = trendData.value[trendData.value.length - 1]
      summary.value = {
        total_co2_kg: last.total_co2_kg ?? '--',
        total_extra_co2_kg: last.extra_co2_kg ?? '--',
        sections_count: last.sections_count ?? '--',
        avg_speed: '--',
      }
    }
    // fetch current for avg_speed
    try {
      const curRes = await carbonApi.getCurrent()
      const cur = curRes.data || curRes
      if (cur) {
        summary.value.avg_speed = cur.avg_speed ?? '--'
        if (cur.total_co2_kg) summary.value.total_co2_kg = cur.total_co2_kg
        if (cur.total_extra_co2_kg) summary.value.total_extra_co2_kg = cur.total_extra_co2_kg
        if (cur.sections_count) summary.value.sections_count = cur.sections_count
      }
    } catch { /* ignore */ }
  } catch { trendData.value = [] }
  loadingTrend.value = false
  await nextTick()
  renderCharts()
}

async function loadTop() {
  loadingTop.value = true
  try {
    const res = await carbonApi.getSectionTop(10)
    const data = res.data || res
    topData.value = data.items || data || []
  } catch { topData.value = [] }
  loadingTop.value = false
  await nextTick()
  renderTopChart()
}

function renderCharts() {
  if (!trendChartRef.value || !stackedChartRef.value) return
  if (!trendData.value.length) return

  const labels = trendData.value.map(d => {
    const t = d.timestamp || ''
    return period.value === 'day' ? t.slice(11, 16) || t : t.slice(5, 10) || t
  })
  const total = trendData.value.map(d => d.total_co2_kg ?? 0)
  const normal = trendData.value.map(d => d.normal_co2_kg ?? 0)
  const extra = trendData.value.map(d => d.extra_co2_kg ?? 0)

  // Trend line
  if (!trendChart) trendChart = echarts.init(trendChartRef.value)
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['总排放', '正常排放', '额外排放'], textStyle: { color: '#8899aa' } },
    grid: { left: 50, right: 20, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: labels, axisLabel: { color: '#8899aa', rotate: 45 } },
    yAxis: { type: 'value', name: 'CO₂ (kg/h)', nameTextStyle: { color: '#8899aa' }, axisLabel: { color: '#8899aa' } },
    series: [
      { name: '总排放', type: 'line', smooth: true, data: total, lineStyle: { color: '#f44336', width: 2 }, itemStyle: { color: '#f44336' }, symbol: 'none' },
      { name: '正常排放', type: 'line', smooth: true, data: normal, lineStyle: { color: '#00e676', width: 2 }, itemStyle: { color: '#00e676' }, symbol: 'none' },
      { name: '额外排放', type: 'line', smooth: true, data: extra, lineStyle: { color: '#ff9800', width: 2, type: 'dashed' }, itemStyle: { color: '#ff9800' }, symbol: 'none' },
    ],
  })

  // Stacked bar
  if (!stackedChart) stackedChart = echarts.init(stackedChartRef.value)
  stackedChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['正常排放', '拥堵额外排放'], textStyle: { color: '#8899aa' } },
    grid: { left: 50, right: 20, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: labels, axisLabel: { color: '#8899aa', rotate: 45 } },
    yAxis: { type: 'value', name: 'CO₂ (kg/h)', nameTextStyle: { color: '#8899aa' }, axisLabel: { color: '#8899aa' } },
    series: [
      { name: '正常排放', type: 'bar', stack: 'total', data: normal, itemStyle: { color: '#00e676' } },
      { name: '拥堵额外排放', type: 'bar', stack: 'total', data: extra, itemStyle: { color: '#ff9800' } },
    ],
  })
}

function renderTopChart() {
  if (!topChartRef.value || !topData.value.length) return
  if (!topChart) topChart = echarts.init(topChartRef.value)

  const names = topData.value.map(d => d.section_name || `路段${d.section_id}`).reverse()
  const values = topData.value.map(d => d.total_co2_kg ?? 0).reverse()
  const extras = topData.value.map(d => d.extra_co2_kg ?? 0).reverse()

  topChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['总排放', '额外排放'], textStyle: { color: '#8899aa' } },
    grid: { left: 100, right: 20, top: 20, bottom: 20 },
    xAxis: { type: 'value', name: 'CO₂ (kg/h)', nameTextStyle: { color: '#8899aa' }, axisLabel: { color: '#8899aa' } },
    yAxis: { type: 'category', data: names, axisLabel: { color: '#8899aa' } },
    series: [
      { name: '总排放', type: 'bar', data: values, itemStyle: { color: '#f44336' }, barWidth: 12 },
      { name: '额外排放', type: 'bar', data: extras, itemStyle: { color: '#ff9800' }, barWidth: 12 },
    ],
  })
}

onMounted(async () => {
  await loadData()
  await loadTop()
})

onUnmounted(() => {
  trendChart?.dispose()
  stackedChart?.dispose()
  topChart?.dispose()
})
</script>

<style scoped>
.carbon-view { padding: 0; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.page-header h2 { color: var(--text-primary); margin: 0; font-size: 20px; }

.stats-row { margin-bottom: 20px; }
.stat-card { background: var(--bg-panel); border: 1px solid rgba(255,255,255,0.06); text-align: center; padding: 8px 0; }
.stat-value { font-size: 28px; font-weight: 700; color: var(--text-primary); font-variant-numeric: tabular-nums; }
.stat-value.extra { color: #ff9800; }
.stat-label { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }

.chart-card { background: var(--bg-panel); border: 1px solid rgba(255,255,255,0.06); margin-bottom: 20px; }
.chart-container { height: 300px; }
.top-chart { height: 350px; }
.top-card { margin-bottom: 0; }
</style>
