<template>
  <div ref="mapContainer" class="traffic-map" style="width:100%;height:500px;border-radius:8px;overflow:hidden">
    <div v-if="!mapReady && !loadError" style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-secondary)">
      <el-icon class="is-loading" :size="24"><Loading /></el-icon>
      <span style="margin-left:8px">地图加载中...</span>
    </div>
    <div v-if="loadError" style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:var(--text-secondary);text-align:center">
      <div style="font-size:48px;margin-bottom:16px">🗺️</div>
      <div style="font-size:16px;font-weight:bold;margin-bottom:8px">地图未配置</div>
      <div style="font-size:13px;max-width:300px;line-height:1.6">
        需要在 <code>.env.development</code> 中配置高德地图 Key。<br/>
        前往 <a href="https://lbs.amap.com" target="_blank" style="color:var(--accent-blue)">lbs.amap.com</a> 申请免费Key。
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { Loading } from '@element-plus/icons-vue'

const props = defineProps({
  sections: { type: Array, default: () => [] },
  mapHeight: { type: String, default: '500px' },
})
const emit = defineEmits(['section-click'])

const mapContainer = ref(null)
const mapInstance = ref(null)
const mapReady = ref(false)
const loadError = ref(false)
const markers = ref([])

const AMAP_KEY = import.meta.env.VITE_AMAP_KEY

const loadAMapScript = () => {
  return new Promise((resolve, reject) => {
    if (window.AMap) return resolve()
    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${AMAP_KEY}&plugin=AMap.Marker`
    script.onload = resolve
    script.onerror = () => reject(new Error('高德地图加载失败：请检查 Key 是否正确'))
    document.head.appendChild(script)
  })
}

const addMarkers = () => {
  if (!mapInstance.value) return
  markers.value.forEach(m => mapInstance.value.remove(m))
  markers.value = []
  props.sections.forEach(s => {
    if (s.coordinates?.start) {
      const pos = [s.coordinates.start[0], s.coordinates.start[1]]
      const marker = new AMap.Marker({ position: pos, title: s.name })
      marker.on('click', () => emit('section-click', s))
      mapInstance.value.add(marker)
      markers.value.push(marker)
    }
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
    addMarkers()
  } catch (err) {
    console.warn('[TrafficMap]', err.message)
    loadError.value = true
  }
})

watch(() => props.sections, () => { if (mapReady.value) addMarkers() }, { deep: true })

onUnmounted(() => {
  mapInstance.value?.destroy()
  mapInstance.value = null
})
</script>
