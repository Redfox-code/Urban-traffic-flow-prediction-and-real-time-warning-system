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
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  sections: { type: Array, default: () => [] },
  mapHeight: { type: String, default: '500px' },
})
const emit = defineEmits(['section-click'])

import { Loading } from '@element-plus/icons-vue'

const mapContainer = ref(null)
const mapInstance = ref(null)
const mapReady = ref(false)
const loadError = ref(false)

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
    // D7: 添加路段标注点
    props.sections.forEach((section, i) => {
      if (section.coordinates) {
        const pos = section.coordinates.start || section.coordinates
        const marker = new AMap.Marker({ position: pos, title: section.name, label: { content: section.name, direction: 'top' } })
        marker.on('click', () => emit('section-click', section))
        mapInstance.value.add(marker)
      }
    })
    mapInstance.value.on('click', (e) => {
      // D8: 点击路段 → 联动ECharts
    })
  } catch (err) {
    console.warn('[TrafficMap]', err.message)
    loadError.value = true
  }
})

onUnmounted(() => {
  mapInstance.value?.destroy()
  mapInstance.value = null
})
</script>
