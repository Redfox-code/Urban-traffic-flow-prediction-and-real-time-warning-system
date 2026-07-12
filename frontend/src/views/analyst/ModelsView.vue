<template>
  <div class="models-view">
    <div class="page-header">
      <h2>模型管理</h2>
      <el-button type="primary" :loading="retraining" @click="handleRetrain">
        <span v-if="!retraining">重新训练</span>
        <span v-else>训练中...</span>
      </el-button>
    </div>

    <!-- 模型状态卡片 -->
    <el-row :gutter="20" class="model-cards">
      <el-col :span="12" v-for="m in modelTypes" :key="m.key">
        <el-card class="model-card" :class="`model-${m.key}`">
          <template #header>
            <div class="card-header">
              <span class="model-name">{{ m.label }}</span>
              <el-tag :type="statusType(m.key)" effect="dark" size="small">
                {{ m.key === 'KNN' ? accuracy?.models?.KNN?.mae ? '已就绪' : '未训练' :
                       accuracy?.models?.RF?.mae ? '已就绪' : '未训练' }}
              </el-tag>
            </div>
          </template>
          <div class="model-body">
            <div class="metrics-grid">
              <div class="metric-item">
                <span class="metric-label">MAE</span>
                <span class="metric-value">{{ getMetric(m.key, 'mae') }}</span>
              </div>
              <div class="metric-item">
                <span class="metric-label">RMSE</span>
                <span class="metric-value">{{ getMetric(m.key, 'rmse') }}</span>
              </div>
              <div class="metric-item">
                <span class="metric-label">MAPE</span>
                <span class="metric-value">{{ getMetric(m.key, 'mape') }}%</span>
              </div>
              <div class="metric-item">
                <span class="metric-label">R²</span>
                <span class="metric-value">{{ getMetric(m.key, 'r2') }}</span>
              </div>
            </div>
            <div class="model-footer-info">
              <span class="update-label">最后更新: {{ accuracy?.updated_at ? formatTime(accuracy.updated_at) : '--' }}</span>
              <span class="best-badge" v-if="accuracy?.best_model === m.key">最佳模型</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 精度趋势图 + 参数调优 -->
    <el-row :gutter="20" class="charts-row">
      <el-col :span="14">
        <el-card class="chart-card">
          <template #header>精度趋势（过去7天MAE）</template>
          <div ref="trendChartRef" class="chart-container" v-loading="loading"></div>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card class="params-card">
          <template #header>参数调优</template>
          <div class="params-form">
            <div class="param-group">
              <h4>KNN</h4>
              <div class="param-item">
                <label>K值: {{ knnParams.k }}</label>
                <el-slider v-model="knnParams.k" :min="1" :max="20" :step="1" />
              </div>
            </div>
            <div class="param-group">
              <h4>随机森林</h4>
              <div class="param-item">
                <label>n_estimators: {{ rfParams.n_estimators }}</label>
                <el-slider v-model="rfParams.n_estimators" :min="50" :max="300" :step="10" />
              </div>
              <div class="param-item">
                <label>max_depth: {{ rfParams.max_depth }}</label>
                <el-slider v-model="rfParams.max_depth" :min="5" :max="30" :step="1" />
              </div>
            </div>
            <el-button type="primary" size="small" @click="handleApplyParams" :disabled="true">
              应用参数（需重新训练）
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { predictionApi } from '@/api/prediction'
import * as echarts from 'echarts/core'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent, CanvasRenderer])

const modelTypes = [
  { key: 'KNN', label: 'KNN (K近邻)' },
  { key: 'RF', label: '随机森林 (Random Forest)' },
]

const loading = ref(false)
const retraining = ref(false)
const accuracy = ref(null)
const trendChartRef = ref(null)
let trendChart = null

const knnParams = reactive({ k: 5 })
const rfParams = reactive({ n_estimators: 100, max_depth: 10 })

function getMetric(modelKey, metric) {
  const m = accuracy.value?.models?.[modelKey]
  return m && m[metric] !== undefined ? m[metric] : '--'
}

function statusType(modelKey) {
  const m = accuracy.value?.models?.[modelKey]
  return m?.mae ? 'success' : 'info'
}

function formatTime(ts) {
  if (!ts) return '--'
  try { return new Date(ts).toLocaleString('zh-CN') } catch { return ts }
}

async function loadAccuracy() {
  loading.value = true
  try {
    const res = await predictionApi.getAccuracy()
    accuracy.value = res.data || res
  } catch { /* keep defaults */ }
  loading.value = false
}

function renderTrendChart() {
  if (!trendChartRef.value) return
  if (!trendChart) trendChart = echarts.init(trendChartRef.value)

  // generate mock 7-day MAE data for both models
  const days = ['7日前', '6日前', '5日前', '4日前', '3日前', '昨日', '今日']
  const rfMae = accuracy.value?.models?.RF?.mae || 8.7
  const knnMae = accuracy.value?.models?.KNN?.mae || 12.3
  const rfData = days.map((_, i) => Math.max(0, rfMae + (Math.random() - 0.5) * 3))
  const knnData = days.map((_, i) => Math.max(0, knnMae + (Math.random() - 0.5) * 4))

  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['RF MAE', 'KNN MAE', '告警阈值'], textStyle: { color: '#8899aa' } },
    grid: { left: 50, right: 20, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: days, axisLabel: { color: '#8899aa' } },
    yAxis: {
      type: 'value', name: 'MAE (veh/h)', nameTextStyle: { color: '#8899aa' },
      axisLabel: { color: '#8899aa' },
    },
    series: [
      {
        name: 'RF MAE', type: 'line', smooth: true, data: rfData,
        lineStyle: { color: '#00d4ff', width: 2 },
        itemStyle: { color: '#00d4ff' }, symbol: 'circle', symbolSize: 6,
      },
      {
        name: 'KNN MAE', type: 'line', smooth: true, data: knnData,
        lineStyle: { color: '#ff9800', width: 2 },
        itemStyle: { color: '#ff9800' }, symbol: 'diamond', symbolSize: 6,
      },
      {
        name: '告警阈值', type: 'line', data: days.map(() => 15),
        lineStyle: { color: '#f44336', width: 2, type: 'dashed' },
        symbol: 'none',
      },
    ],
  })
}

async function handleRetrain() {
  retraining.value = true
  // Simulate retrain call -- backend would handle async
  await new Promise(resolve => setTimeout(resolve, 2000))
  window.__updateModelStatus?.('training')
  await new Promise(resolve => setTimeout(resolve, 1500))
  await loadAccuracy()
  renderTrendChart()
  window.__updateModelStatus?.('ready')
  retraining.value = false
}

function handleApplyParams() {
  // Placeholder: params applied on next retrain
}

onMounted(async () => {
  await loadAccuracy()
  await nextTick()
  renderTrendChart()
  window.addEventListener('resize', () => trendChart?.resize())
})

onUnmounted(() => {
  trendChart?.dispose()
  window.removeEventListener('resize', () => trendChart?.resize())
})
</script>

<style scoped>
.models-view { padding: 0; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.page-header h2 { color: var(--text-primary); margin: 0; font-size: 20px; }

.model-cards { margin-bottom: 20px; }
.model-card { background: var(--bg-panel); border: 1px solid rgba(255,255,255,0.06); }
.card-header { display: flex; align-items: center; justify-content: space-between; }
.model-name { font-size: 16px; font-weight: 600; color: var(--text-primary); }

.metrics-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.metric-item { display: flex; flex-direction: column; gap: 4px; }
.metric-label { font-size: 12px; color: var(--text-secondary); }
.metric-value { font-size: 22px; font-weight: 700; color: var(--text-primary); font-variant-numeric: tabular-nums; }

.model-footer-info { display: flex; align-items: center; justify-content: space-between; margin-top: 16px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.06); }
.update-label { font-size: 12px; color: var(--text-secondary); }
.best-badge { background: rgba(0, 230, 118, 0.15); color: #00e676; padding: 2px 10px; border-radius: 10px; font-size: 11px; font-weight: 600; }

.charts-row { margin-bottom: 0; }
.chart-card { background: var(--bg-panel); border: 1px solid rgba(255,255,255,0.06); }
.chart-container { height: 320px; }

.params-card { background: var(--bg-panel); border: 1px solid rgba(255,255,255,0.06); }
.params-form { display: flex; flex-direction: column; gap: 16px; }
.param-group h4 { color: var(--text-primary); margin: 0 0 12px; font-size: 14px; }
.param-item { margin-bottom: 12px; }
.param-item label { font-size: 13px; color: var(--text-secondary); display: block; margin-bottom: 6px; }
</style>
