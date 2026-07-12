<template>
  <div class="intersection-topology">
    <div class="it-header">
      <span class="it-title">{{ intersectionName || '交叉口拓扑' }}</span>
      <el-tag v-if="data.phase" size="small" effect="dark" type="info">
        当前配时: {{ data.phase }}s
      </el-tag>
    </div>
    <canvas ref="topoCanvas" class="it-canvas" :width="canvasSize" :height="canvasSize"></canvas>
    <div class="it-footer" v-if="data.suggestedPhase">
      <span style="font-size:12px;color:var(--text-secondary)">建议配时</span>
      <div class="it-phase-bar">
        <div class="it-phase-seg" v-for="(seg, i) in phases" :key="i"
             :style="{ width: seg.pct + '%', background: seg.color }">
          {{ seg.label }} {{ seg.seconds }}s
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'

const props = defineProps({
  intersectionName: { type: String, default: '' },
  data: { type: Object, default: () => ({
    north: { flow: 0, direction: '北' },
    south: { flow: 0, direction: '南' },
    east: { flow: 0, direction: '东' },
    west: { flow: 0, direction: '西' },
    phase: null,
    suggestedPhase: null, // [{direction, seconds, color}]
  })},
  canvasSize: { type: Number, default: 260 },
})

const topoCanvas = ref(null)

const phases = computed(() => {
  if (!props.data.suggestedPhase) return []
  const total = props.data.suggestedPhase.reduce((s, p) => s + p.seconds, 0) || 1
  return props.data.suggestedPhase.map(p => ({
    ...p,
    pct: (p.seconds / total) * 100,
  }))
})

// 获取进口道流量值
const approaches = computed(() => [
  { ...props.data.north, key: 'north' },
  { ...props.data.south, key: 'south' },
  { ...props.data.east, key: 'east' },
  { ...props.data.west, key: 'west' },
])

const drawTopology = () => {
  const canvas = topoCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const size = canvas.width
  const cx = size / 2
  const cy = size / 2
  const roadW = 48
  const armLen = 70

  ctx.clearRect(0, 0, size, size)

  // 背景
  ctx.fillStyle = 'rgba(10,22,40,.9)'
  ctx.fillRect(0, 0, size, size)

  // 绘制四向道路
  ctx.fillStyle = 'rgba(255,255,255,.08)'
  // 水平道路
  ctx.fillRect(cx - armLen - 20, cy - roadW / 2, (armLen + 20) * 2, roadW)
  // 垂直道路
  ctx.fillRect(cx - roadW / 2, cy - armLen - 20, roadW, (armLen + 20) * 2)

  // 交叉口中心
  ctx.fillStyle = 'rgba(0,0,0,.4)'
  ctx.fillRect(cx - roadW / 2, cy - roadW / 2, roadW, roadW)
  ctx.strokeStyle = 'rgba(255,255,255,.2)'
  ctx.lineWidth = 1
  ctx.strokeRect(cx - roadW / 2, cy - roadW / 2, roadW, roadW)

  // 方向箭头和流量
  const dirs = [
    { x: 0, y: -1, label: '北', flow: props.data.north?.flow || 0, angle: 0 },
    { x: 0, y: 1, label: '南', flow: props.data.south?.flow || 0, angle: Math.PI },
    { x: -1, y: 0, label: '西', flow: props.data.west?.flow || 0, angle: -Math.PI / 2 },
    { x: 1, y: 0, label: '东', flow: props.data.east?.flow || 0, angle: Math.PI / 2 },
  ]

  dirs.forEach(dir => {
    const ax = cx + dir.x * (armLen + 10)
    const ay = cy + dir.y * (armLen + 10)

    // 箭头
    ctx.save()
    ctx.translate(ax, ay)
    ctx.rotate(dir.angle)
    ctx.beginPath()
    ctx.moveTo(10, 0)
    ctx.lineTo(-6, -8)
    ctx.lineTo(-6, 8)
    ctx.closePath()
    ctx.fillStyle = 'rgba(0,212,255,.7)'
    ctx.fill()
    ctx.restore()

    // 路名
    ctx.fillStyle = 'rgba(255,255,255,.5)'
    ctx.font = '11px sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = dir.y === 0 ? 'middle' : (dir.y < 0 ? 'bottom' : 'top')
    ctx.fillText(dir.label, ax, ay + (dir.y === 0 ? -16 : 0))

    // 流量值
    ctx.fillStyle = '#00e676'
    ctx.font = 'bold 13px sans-serif'
    ctx.textBaseline = dir.y === 0 ? 'middle' : (dir.y < 0 ? 'top' : 'bottom')
    ctx.fillText(dir.flow + ' veh', ax, ay + (dir.y === 0 ? 16 : (dir.y < 0 ? 18 : -18)))
  })

  // 当前配时（如果有）
  if (props.data.phase) {
    ctx.fillStyle = 'rgba(0,212,255,.6)'
    ctx.font = 'bold 14px sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(props.data.phase + 's', cx, cy)
  }
}

watch(() => props.data, () => {
  nextTick(drawTopology)
}, { deep: true })

onMounted(() => {
  nextTick(drawTopology)
})
</script>

<style scoped>
.intersection-topology {
  background: var(--bg-panel);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 12px;
  overflow: hidden;
}
.it-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  border-bottom: 1px solid rgba(255,255,255,.06);
}
.it-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.it-canvas {
  display: block;
  width: 100%;
  height: auto;
}
.it-footer {
  padding: 10px 14px;
  border-top: 1px solid rgba(255,255,255,.06);
}
.it-phase-bar {
  display: flex;
  height: 20px;
  border-radius: 4px;
  overflow: hidden;
  margin-top: 4px;
}
.it-phase-seg {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: #fff;
  font-weight: bold;
}
</style>
