<template>
  <canvas ref="rippleCanvas" class="propagation-ripple" :style="canvasStyle"></canvas>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'

const props = defineProps({
  map: { type: Object, required: true },
  sources: { type: Array, default: () => [] }, // [{center:[lng,lat], level:'jammed'|'congested', delay:3}]
  visible: { type: Boolean, default: true },
})

const rippleCanvas = ref(null)
let animationId = null
let ripples = [] // 活跃涟漪
const mapContainer = ref(null)

const canvasStyle = computed(() => ({
  display: props.visible ? 'block' : 'none',
}))

// 颜色映射
const levelColors = {
  jammed: { r: 245, g: 34, b: 45, label: '严重拥堵' },
  congested: { r: 250, g: 140, b: 22, label: '拥堵' },
  slow: { r: 250, g: 219, b: 20, label: '缓行' },
}

// 创建涟漪
const createRipple = (source) => {
  if (!props.map || !rippleCanvas.value) return
  const pixel = props.map.lngLatToContainer(source.center)
  if (!pixel) return
  const color = levelColors[source.level] || levelColors.jammed
  ripples.push({
    x: pixel.getX(),
    y: pixel.getY(),
    radius: 0,
    maxRadius: 80 + (source.delay || 3) * 10,
    speed: 0.8 + (source.delay || 3) * 0.15,
    opacity: 0.8,
    color,
    startTime: Date.now(),
    duration: 2000 + (source.delay || 3) * 500,
  })
}

// 地图移动时更新涟漪位置
const updateRipplePositions = () => {
  if (!props.map || !props.sources.length) return
  props.sources.forEach((source, idx) => {
    if (ripples[idx]) {
      const pixel = props.map.lngLatToContainer(source.center)
      if (pixel) {
        ripples[idx].x = pixel.getX()
        ripples[idx].y = pixel.getY()
      }
    }
  })
}

// Canvas渲染循环
const animate = () => {
  if (!rippleCanvas.value) return
  const canvas = rippleCanvas.value
  const ctx = canvas.getContext('2d')
  const w = canvas.width
  const h = canvas.height

  ctx.clearRect(0, 0, w, h)

  const now = Date.now()

  // 移除过期涟漪，生成新环
  ripples = ripples.filter(r => {
    const elapsed = now - r.startTime
    if (elapsed > r.duration) {
      if (props.sources.length > 0) {
        // 重新生成
        setTimeout(() => {
          const srcIdx = ripples.length < props.sources.length ? ripples.length : 0
          if (props.sources[srcIdx]) createRipple(props.sources[srcIdx])
        }, 100)
      }
      return false
    }
    return true
  })

  // 绘制涟漪
  ripples.forEach(r => {
    const progress = (now - r.startTime) / r.duration
    const currentRadius = r.maxRadius * progress
    const currentOpacity = r.opacity * (1 - progress)

    if (currentOpacity <= 0) return

    // 外圈（渐变红→橙→透明）
    const gradient = ctx.createRadialGradient(r.x, r.y, 0, r.x, r.y, currentRadius)
    gradient.addColorStop(0, `rgba(${r.color.r},${r.color.g},${r.color.b},${currentOpacity * 0.6})`)
    gradient.addColorStop(0.4, `rgba(${r.color.r},${r.color.g * 0.7},${r.color.b},${currentOpacity * 0.4})`)
    gradient.addColorStop(0.7, `rgba(${r.color.r * 0.8},${r.color.g * 0.4},${0},${currentOpacity * 0.2})`)
    gradient.addColorStop(1, `rgba(${r.color.r * 0.5},${0},${0},0)`)

    ctx.beginPath()
    ctx.arc(r.x, r.y, currentRadius, 0, Math.PI * 2)
    ctx.fillStyle = gradient
    ctx.fill()

    // 圆环
    ctx.beginPath()
    ctx.arc(r.x, r.y, currentRadius * 0.85, 0, Math.PI * 2)
    ctx.strokeStyle = `rgba(${r.color.r},${r.color.g},${r.color.b},${currentOpacity * 0.5})`
    ctx.lineWidth = 2
    ctx.stroke()

    // 内圈
    ctx.beginPath()
    ctx.arc(r.x, r.y, currentRadius * 0.25, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(${r.color.r},${r.color.g},${r.color.b},${currentOpacity * 0.3})`
    ctx.fill()
  })

  animationId = requestAnimationFrame(animate)
}

// 调整Canvas尺寸
const resizeCanvas = () => {
  if (!rippleCanvas.value || !props.map) return
  const container = props.map.getContainer()
  if (container) {
    rippleCanvas.value.width = container.offsetWidth
    rippleCanvas.value.height = container.offsetHeight
  }
}

// 监听地图事件
const bindMapEvents = () => {
  if (!props.map) return
  props.map.on('moveend', updateRipplePositions)
  props.map.on('resize', resizeCanvas)
}

const unbindMapEvents = () => {
  if (!props.map) return
  props.map.off('moveend', updateRipplePositions)
  props.map.off('resize', resizeCanvas)
}

watch(() => props.sources, (val) => {
  if (val.length > 0) {
    val.forEach(src => createRipple(src))
  }
}, { deep: true })

watch(() => props.visible, (val) => {
  if (val) {
    resizeCanvas()
  }
})

onMounted(() => {
  nextTick(() => {
    resizeCanvas()
    bindMapEvents()
    animate()
    // 初始创建涟漪
    props.sources.forEach(src => createRipple(src))
  })
})

onUnmounted(() => {
  cancelAnimationFrame(animationId)
  unbindMapEvents()
})
</script>

<style scoped>
.propagation-ripple {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 50;
  pointer-events: none;
}
</style>
