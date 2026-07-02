<template>
  <div ref="mapContainer" class="traffic-map" style="width:100%;height:500px;border-radius:8px;overflow:hidden">
    <div v-if="!mapReady" style="color:var(--text-secondary);padding:20px">🗺️ 地图加载中...</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  sections: { type: Array, default: () => [] },
  mapHeight: { type: String, default: '500px' },
})
const emit = defineEmits(['section-click'])

const mapContainer = ref(null)
const mapInstance = ref(null)
const mapReady = ref(false)

const AMAP_KEY = import.meta.env.VITE_AMAP_KEY

const loadAMapScript = () => {
  return new Promise((resolve, reject) => {
    if (window.AMap) return resolve()
    // 用户需在高德开放平台申请Key，替换.env.development中的VITE_AMAP_KEY
    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/v2/maps?v=2.0&key=${AMAP_KEY}&plugin=AMap.HeatMap`
    script.onload = resolve
    script.onerror = () => reject(new Error('高德地图加载失败：请检查 VITE_AMAP_KEY'))
    document.head.appendChild(script)
  })
}

onMounted(async () => {
  try {
    await loadAMapScript()
    mapInstance.value = new AMap.Map(mapContainer.value, {
      zoom: 13,
      center: [116.397, 39.908],
      mapStyle: 'amap://styles/darkblue',
      resizeEnable: true,
    })
    mapReady.value = true
    mapInstance.value.on('click', (e) => {
      // TODO D8: 点击路段 → emit section-click → ECharts联动
    })
  } catch (err) {
    console.warn('[TrafficMap]', err.message)
  }
})

onUnmounted(() => {
  mapInstance.value?.destroy()
  mapInstance.value = null
})
</script>
