<template>
  <div class="section-info-card">
    <div class="sic-header">
      <h3 class="sic-title">{{ data.name || '未知路段' }}</h3>
      <el-tag :type="levelTagType" size="small" effect="dark">{{ levelLabel }}</el-tag>
    </div>

    <div class="sic-metrics">
      <div class="sic-metric">
        <span class="sic-metric-label">车流量</span>
        <span class="sic-metric-value">{{ data.vehicle_count ?? '--' }} <small>veh</small></span>
      </div>
      <div class="sic-metric">
        <span class="sic-metric-label">平均速度</span>
        <span class="sic-metric-value">{{ data.avg_speed ?? '--' }} <small>km/h</small></span>
      </div>
      <div class="sic-metric">
        <span class="sic-metric-label">拥堵指数</span>
        <span class="sic-metric-value">{{ data.occupancy ?? '--' }}<small>%</small></span>
      </div>
      <div class="sic-metric">
        <span class="sic-metric-label">趋势</span>
        <span class="sic-metric-value" :style="{ color: trendColor }">{{ trendLabel }}</span>
      </div>
    </div>

    <!-- 迷你折线图（过去2h + 未来1h预测） -->
    <div class="sic-sparkline">
      <div class="sic-sparkline-title">流量趋势</div>
      <canvas ref="sparkCanvas" width="280" height="50"></canvas>
      <div class="sic-sparkline-labels">
        <span>过去2h</span>
        <span style="color:var(--accent-blue)">预测</span>
      </div>
    </div>

    <div class="sic-actions">
      <el-button size="small" type="primary" plain @click="$emit('view-detail', data)">查看详情</el-button>
      <el-button size="small" plain @click="$emit('surrounding', data)">周边路况</el-button>
      <el-button size="small" plain @click="$emit('signal-optimize', data)">信号优化</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps({
  data: { type: Object, default: () => ({
    name: '', id: null, vehicle_count: 0, avg_speed: 0, occupancy: 0,
    history: [], forecast: [], trend: 'stable'
  })}
})

defineEmits(['view-detail', 'surrounding', 'signal-optimize'])

const sparkCanvas = ref(null)

const levelTagType = computed(() => {
  const occ = props.data.occupancy ?? 0
  if (occ < 30) return 'success'
  if (occ < 60) return 'warning'
  if (occ < 85) return 'warning'
  return 'danger'
})

const levelLabel = computed(() => {
  const occ = props.data.occupancy ?? 0
  if (occ < 30) return '畅通'
  if (occ < 60) return '缓行'
  if (occ < 85) return '拥堵'
  return '严重拥堵'
})

const trendLabel = computed(() => {
  const map = { up: '上升', down: '下降', stable: '平稳' }
  return map[props.data.trend] || '平稳'
})

const trendColor = computed(() => {
  const map = { up: '#f5222d', down: '#52c41a', stable: '#fadb14' }
  return map[props.data.trend] || '#8899aa'
})

const drawSparkline = () => {
  const canvas = sparkCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const w = canvas.width
  const h = canvas.height
  const padding = { top: 8, bottom: 12, left: 8, right: 8 }
  const plotW = w - padding.left - padding.right
  const plotH = h - padding.top - padding.bottom

  ctx.clearRect(0, 0, w, h)

  const history = props.data.history || []
  const forecast = props.data.forecast || []
  const all = [...history, ...forecast]
  if (all.length < 2) return

  const maxVal = Math.max(...all, 1)
  const minVal = Math.min(...all, 0)
  const range = maxVal - minVal || 1

  // 绘制历史数据（实线，青绿色）
  ctx.beginPath()
  ctx.strokeStyle = '#00e676'
  ctx.lineWidth = 2
  history.forEach((v, i) => {
    const x = padding.left + (i / (history.length - 1 || 1)) * plotW
    const y = padding.top + plotH - ((v - minVal) / range) * plotH
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
  })
  ctx.stroke()

  // 绘制预测数据（虚线，蓝色）
  if (forecast.length > 0) {
    ctx.beginPath()
    ctx.strokeStyle = '#00d4ff'
    ctx.lineWidth = 2
    ctx.setLineDash([4, 3])
    const startIdx = history.length
    forecast.forEach((v, i) => {
      const x = padding.left + ((startIdx + i) / (all.length - 1 || 1)) * plotW
      const y = padding.top + plotH - ((v - minVal) / range) * plotH
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
    })
    ctx.stroke()
    ctx.setLineDash([])
  }

  // 分界线
  ctx.beginPath()
  ctx.strokeStyle = 'rgba(255,255,255,0.15)'
  ctx.lineWidth = 1
  const splitX = padding.left + (history.length / (all.length - 1 || 1)) * plotW
  ctx.moveTo(splitX, padding.top)
  ctx.lineTo(splitX, padding.top + plotH)
  ctx.stroke()
}

watch(() => [props.data.history, props.data.forecast], () => {
  nextTick(drawSparkline)
}, { deep: true })

watch(sparkCanvas, (val) => {
  if (val) nextTick(drawSparkline)
})

// 初始渲染
nextTick(drawSparkline)
</script>

<style scoped>
.section-info-card {
  background: var(--bg-panel);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 12px;
  padding: 16px;
  min-width: 280px;
  color: var(--text-primary);
}
.sic-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.sic-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}
.sic-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 14px;
}
.sic-metric {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.sic-metric-label {
  font-size: 11px;
  color: var(--text-secondary);
  text-transform: uppercase;
}
.sic-metric-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}
.sic-metric-value small {
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 400;
}
.sic-sparkline {
  margin-bottom: 14px;
  padding: 10px;
  background: rgba(0,0,0,.2);
  border-radius: 8px;
}
.sic-sparkline-title {
  font-size: 11px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.sic-sparkline canvas {
  width: 100%;
  height: 50px;
  display: block;
}
.sic-sparkline-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: var(--text-secondary);
  margin-top: 4px;
}
.sic-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
