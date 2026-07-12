<template>
  <!-- 应急路线渲染（无可见DOM，通过高德API渲染） -->
  <div class="emergency-route" style="display:none"></div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  map: { type: Object, required: true },
  route: { type: Object, default: null }, // {path:[[lng,lat]], intersections:[{pos,lng,lat,direction}], startName, endName}
  visible: { type: Boolean, default: true },
})

const emit = defineEmits(['estimated-time'])

let routePolyline = null
let markers = []
let arrowMarkers = []
let flashInterval = null
let flashState = 0

const clearRoute = () => {
  if (routePolyline) { props.map?.remove(routePolyline); routePolyline = null }
  markers.forEach(m => props.map?.remove(m))
  arrowMarkers.forEach(m => props.map?.remove(m))
  markers = []
  arrowMarkers = []
  clearInterval(flashInterval)
  flashInterval = null
}

const buildRoute = () => {
  if (!props.map || !props.route || !props.visible) return
  clearRoute()

  const { path, intersections, startName, endName, estimatedTime, normalTime } = props.route
  if (!path || path.length < 2) return

  // 蓝色粗线
  routePolyline = new AMap.Polyline({
    path,
    strokeColor: '#1890ff',
    strokeWeight: 8,
    strokeOpacity: 0.85,
    lineJoin: 'round',
    lineCap: 'round',
    zIndex: 80,
    showDir: true,
  })
  props.map.add(routePolyline)

  // 闪烁动画（2Hz）
  let flashOn = true
  flashInterval = setInterval(() => {
    flashOn = !flashOn
    routePolyline?.setOptions({
      strokeOpacity: flashOn ? 0.85 : 0.3,
      strokeWeight: flashOn ? 8 : 5,
    })
  }, 500)

  // 起点蓝色标记
  const startPos = path[0]
  if (startPos && window.AMap?.Marker) {
    const startM = new AMap.Marker({
      position: startPos,
      content: `<div class="er-marker er-start"><span>起</span><div class="er-label">${startName || '起点'}</div></div>`,
      offset: new AMap.Pixel(-16, -32),
      zIndex: 90,
    })
    props.map.add(startM)
    markers.push(startM)
  }

  // 终点红色标记
  const endPos = path[path.length - 1]
  if (endPos && window.AMap?.Marker) {
    const endM = new AMap.Marker({
      position: endPos,
      content: `<div class="er-marker er-end"><span>终</span><div class="er-label">${endName || '终点'}</div></div>`,
      offset: new AMap.Pixel(-16, -32),
      zIndex: 90,
    })
    props.map.add(endM)
    markers.push(endM)
  }

  // 路口放行方向箭头
  if (intersections && window.AMap?.Marker) {
    intersections.forEach((int, idx) => {
      const dirMap = { left: '←', right: '→', straight: '↑', uTurn: '↓' }
      const arrow = new AMap.Marker({
        position: int.pos || int.center,
        content: `<div class="er-arrow er-arrow-${int.direction || 'straight'}">${dirMap[int.direction] || '↑'}</div>`,
        offset: new AMap.Pixel(-10, -10),
        zIndex: 85,
      })
      props.map.add(arrow)
      arrowMarkers.push(arrow)
    })
  }

  // 预计vs常规时间对比气泡
  if (estimatedTime || normalTime) {
    const infoContent = `
      <div class="er-time-bubble">
        <div class="er-time-row"><span>预计</span><b>${estimatedTime || '--'} min</b></div>
        <div class="er-time-row"><span>常规</span><b>${normalTime || '--'} min</b></div>
        <div class="er-time-diff">${estimatedTime && normalTime ? ((estimatedTime / normalTime - 1) * 100).toFixed(0) : '--'}%</div>
      </div>`
    const infoWin = new AMap.InfoWindow({
      content: infoContent,
      position: path[Math.floor(path.length / 2)],
      offset: new AMap.Pixel(0, -30),
      closeWhenClickMap: true,
    })
    infoWin.open(props.map)
  }

  // 自适应视野
  props.map.setFitView([routePolyline], false, [60, 60, 60, 200])

  // 发出预计时间事件
  if (estimatedTime || normalTime) {
    emit('estimated-time', { estimatedTime, normalTime })
  }
}

watch(() => props.route, (val) => {
  if (val) buildRoute()
}, { deep: true })

watch(() => props.visible, (val) => {
  if (val) {
    if (props.route) buildRoute()
  } else {
    clearRoute()
  }
})

onMounted(() => {
  if (props.route) buildRoute()
})

onUnmounted(() => {
  clearRoute()
})

defineExpose({ buildRoute, clearRoute })
</script>

<style>
/* 这些都是挂载到地图上的HTML内容，不能用scoped */
.er-marker {
  display: flex; flex-direction: column; align-items: center;
  transform: translate(-50%, -100%);
}
.er-marker span {
  width: 32px; height: 32px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: bold; color: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,.3);
}
.er-start span { background: #1890ff; }
.er-end span { background: #f5222d; }
.er-label {
  font-size: 11px; color: #fff; margin-top: 2px;
  background: rgba(0,0,0,.6); padding: 1px 6px; border-radius: 4px;
  white-space: nowrap;
}
.er-arrow {
  width: 20px; height: 20px; border-radius: 50%;
  background: #1890ff; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: bold;
  box-shadow: 0 1px 4px rgba(0,0,0,.4);
}
.er-arrow-left { background: #1890ff; }
.er-arrow-right { background: #1890ff; }
.er-arrow-straight { background: #52c41a; }
.er-time-bubble {
  background: rgba(0,0,0,.85); border-radius: 8px; padding: 10px 14px;
  color: #e0e6ed; min-width: 120px;
}
.er-time-row {
  display: flex; justify-content: space-between; gap: 16px;
  font-size: 13px; padding: 2px 0;
}
.er-time-row b { color: #00d4ff; }
.er-time-diff {
  text-align: center; margin-top: 6px; padding-top: 6px;
  border-top: 1px solid rgba(255,255,255,.1);
  font-size: 18px; font-weight: bold; color: #ff9800;
}
</style>
