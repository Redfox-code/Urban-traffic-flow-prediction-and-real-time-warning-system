<template>
  <div class="wizard-map">
    <!-- 步骤指示器 -->
    <div class="wm-steps">
      <div v-for="(step, i) in steps" :key="i"
           class="wm-step" :class="{ active: currentStep === i, done: currentStep > i }"
           @click="goToStep(i)">
        <div class="wm-step-circle">{{ currentStep > i ? '✓' : i + 1 }}</div>
        <div class="wm-step-label">{{ step.label }}</div>
      </div>
    </div>

    <!-- 地图容器 -->
    <div ref="mapContainer" class="wm-map"></div>

    <!-- 当前步骤提示 -->
    <div class="wm-hint">
      <div class="wm-hint-icon">{{ steps[currentStep]?.icon }}</div>
      <div class="wm-hint-text">{{ steps[currentStep]?.hint }}</div>
    </div>

    <!-- 底部操作 -->
    <div class="wm-footer">
      <el-button v-if="currentStep > 0" size="small" @click="prevStep">上一步</el-button>
      <el-button v-if="currentStep < steps.length - 1" size="small" type="primary" @click="nextStep"
                 :disabled="!canProceed">下一步</el-button>
      <el-button v-if="currentStep === steps.length - 1" size="small" type="success"
                 :disabled="!canProceed" @click="$emit('complete', wizardData)">完成</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { ROAD_SEGMENTS } from '@/data/roadNetwork'

const emit = defineEmits(['complete', 'step-change'])

const steps = [
  { label: '选起点', icon: '📍', hint: '点击地图选择起点路段', action: 'select-start' },
  { label: '选终点', icon: '🏁', hint: '点击地图选择终点路段', action: 'select-end' },
  { label: '确认路线', icon: '🛣️', hint: '查看规划路线，可拖动调整', action: 'confirm-route' },
  { label: '设置参数', icon: '⚙️', hint: '设置出发时间、车辆类型等', action: 'set-params' },
  { label: '完成', icon: '✅', hint: '确认所有设置，开始导航', action: 'finish' },
]

const currentStep = ref(0)
const canProceed = ref(false)
const mapContainer = ref(null)
const mapInstance = ref(null)
const mapReady = ref(false)

const wizardData = reactive({
  startSection: null,
  endSection: null,
  route: null,
  params: { departureTime: 'now', vehicleType: 'car', avoidToll: false },
})

let currentRoutePolyline = null
let selections = []

const AMAP_KEY = import.meta.env.VITE_AMAP_KEY

const loadAMap = () => {
  return new Promise((resolve, reject) => {
    if (window.AMap) return resolve()
    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${AMAP_KEY}&plugin=AMap.Polyline,AMap.Marker,AMap.InfoWindow`
    script.onload = resolve
    script.onerror = reject
    document.head.appendChild(script)
  })
}

const initMap = async () => {
  try {
    await loadAMap()
    mapInstance.value = new AMap.Map(mapContainer.value, {
      zoom: 14,
      center: [116.4603, 39.9084],
      mapStyle: 'amap://styles/darkblue',
      resizeEnable: true,
    })
    mapReady.value = true
    bindClick()
  } catch (e) {
    console.warn('[WizardMap] 地图加载失败:', e)
  }
}

const bindClick = () => {
  if (!mapInstance.value) return
  mapInstance.value.on('click', (e) => {
    const lnglat = e.lnglat
    if (!lnglat) return
    const nearest = findNearestSection([lnglat.lng, lnglat.lat])
    if (!nearest) return

    if (currentStep.value === 0) {
      wizardData.startSection = nearest
      addSelectionMarker(nearest.path[0], '#00d4ff', '起点')
      canProceed.value = true
    } else if (currentStep.value === 1) {
      if (nearest.id === wizardData.startSection?.id) return
      wizardData.endSection = nearest
      addSelectionMarker(nearest.path[0], '#f5222d', '终点')
      canProceed.value = true
    }
  })
}

// 找最近路段
const findNearestSection = (point) => {
  let minDist = Infinity
  let nearest = null
  ROAD_SEGMENTS.forEach(seg => {
    seg.path.forEach(p => {
      const d = Math.sqrt((p[0] - point[0]) ** 2 + (p[1] - point[1]) ** 2)
      if (d < minDist) { minDist = d; nearest = seg }
    })
  })
  return minDist < 0.01 ? nearest : null
}

const addSelectionMarker = (position, color, label) => {
  if (!mapInstance.value || !window.AMap) return
  const marker = new AMap.Marker({
    position,
    content: `<div style="background:${color};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:bold">${label}</div>`,
    offset: new AMap.Pixel(-16, -12),
    zIndex: 100,
  })
  mapInstance.value.add(marker)
  selections.push(marker)
}

const clearSelections = () => {
  selections.forEach(m => mapInstance.value?.remove(m))
  selections = []
  if (currentRoutePolyline) {
    mapInstance.value?.remove(currentRoutePolyline)
    currentRoutePolyline = null
  }
}

const nextStep = () => {
  if (currentStep.value < steps.length - 1) {
    const prev = currentStep.value
    currentStep.value++
    onStepEnter(currentStep.value)
    emit('step-change', { from: prev, to: currentStep.value })
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    const prev = currentStep.value
    currentStep.value--
    onStepEnter(currentStep.value)
    emit('step-change', { from: prev, to: currentStep.value })
  }
}

const goToStep = (i) => {
  if (i <= currentStep.value) {
    currentStep.value = i
    onStepEnter(i)
  }
}

const onStepEnter = (stepIdx) => {
  canProceed.value = false
  if (stepIdx === 0) {
    clearSelections()
    wizardData.startSection = null
    wizardData.endSection = null
    wizardData.route = null
  } else if (stepIdx === 1 && wizardData.startSection) {
    canProceed.value = !!wizardData.endSection
  } else if (stepIdx === 2 && wizardData.startSection && wizardData.endSection) {
    canProceed.value = true
    buildDemoRoute()
  } else if (stepIdx === 3) {
    canProceed.value = true
  } else if (stepIdx === 4) {
    canProceed.value = true
  }
}

const buildDemoRoute = () => {
  if (!mapInstance.value || !wizardData.startSection || !wizardData.endSection) return
  if (currentRoutePolyline) mapInstance.value.remove(currentRoutePolyline)
  // 随便构造一条路径演示
  const fullPath = [...wizardData.startSection.path, ...wizardData.endSection.path]
  currentRoutePolyline = new AMap.Polyline({
    path: fullPath,
    strokeColor: '#00d4ff',
    strokeWeight: 6,
    strokeOpacity: 0.8,
    lineJoin: 'round',
    zIndex: 90,
  })
  mapInstance.value.add(currentRoutePolyline)
  mapInstance.value.setFitView([currentRoutePolyline])
  wizardData.route = fullPath
}

watch(currentStep, (val) => {
  // 步骤变化时更新界面状态
})

onMounted(initMap)

onUnmounted(() => {
  clearSelections()
  mapInstance.value?.destroy()
})

defineExpose({ wizardData, currentStep, goToStep })
</script>

<style scoped>
.wizard-map {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  background: var(--bg-dark);
}
.wm-steps {
  display: flex;
  justify-content: center;
  gap: 0;
  padding: 16px 20px;
  background: var(--bg-panel);
  border-bottom: 1px solid rgba(255,255,255,.06);
  position: relative;
  z-index: 10;
}
.wm-step {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 16px;
  position: relative;
  opacity: .5;
  transition: opacity .3s;
}
.wm-step.active, .wm-step.done { opacity: 1; }
.wm-step:not(:last-child)::after {
  content: '';
  position: absolute;
  right: -8px;
  top: 50%;
  width: 16px;
  height: 2px;
  background: rgba(255,255,255,.15);
}
.wm-step.done::after { background: var(--accent-blue); }
.wm-step-circle {
  width: 24px; height: 24px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: bold;
  background: rgba(255,255,255,.1);
  color: var(--text-secondary);
  transition: all .3s;
}
.wm-step.active .wm-step-circle {
  background: var(--accent-blue);
  color: #000;
}
.wm-step.done .wm-step-circle {
  background: #52c41a;
  color: #fff;
}
.wm-step-label {
  font-size: 13px;
  color: var(--text-primary);
  white-space: nowrap;
}
.wm-map {
  width: 100%;
  height: 400px;
}
.wm-hint {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: rgba(0,212,255,.08);
  border-top: 1px solid rgba(0,212,255,.15);
}
.wm-hint-icon { font-size: 20px; }
.wm-hint-text { font-size: 14px; color: var(--text-primary); }
.wm-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 16px;
  background: var(--bg-panel);
  border-top: 1px solid rgba(255,255,255,.06);
}
</style>
