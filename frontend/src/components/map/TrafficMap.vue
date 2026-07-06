<template>
  <div ref="mapContainer" class="traffic-map" :style="{width:'100%',height:mapHeight,borderRadius:'8px',overflow:'hidden',position:'relative'}">
    <!-- 加载中 -->
    <div v-if="!mapReady && !loadError" class="map-overlay">
      <el-icon class="is-loading" :size="24"><Loading /></el-icon>
      <span style="margin-left:8px">地图加载中...</span>
    </div>
    <!-- 未配置 -->
    <div v-if="loadError" class="map-overlay" style="flex-direction:column;text-align:center">
      <div style="font-size:48px;margin-bottom:16px">🗺️</div>
      <div style="font-size:16px;font-weight:bold;margin-bottom:8px">地图未配置</div>
      <div style="font-size:13px;max-width:300px;line-height:1.6">
        需要在 <code>.env.development</code> 中配置高德地图 Key。<br/>
        前往 <a href="https://lbs.amap.com" target="_blank" style="color:var(--accent-blue)">lbs.amap.com</a> 申请免费Key。
      </div>
    </div>
    <!-- 图例 -->
    <div v-if="mapReady" class="map-legend">
      <div class="legend-item"><span class="dot" style="background:#52c41a"></span>畅通 &lt;30%</div>
      <div class="legend-item"><span class="dot" style="background:#fadb14"></span>缓行 &lt;60%</div>
      <div class="legend-item"><span class="dot" style="background:#fa8c16"></span>拥堵 &lt;85%</div>
      <div class="legend-item"><span class="dot" style="background:#f5222d"></span>严重 ≥85%</div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { ROAD_SEGMENTS, getCongestionColor, getCongestionWidth, getCongestionOpacity } from '@/data/roadNetwork'
import { trafficApi } from '@/api/traffic'

const props = defineProps({
  sections: { type: Array, default: () => [] },
  mapHeight: { type: String, default: '500px' },
})
const emit = defineEmits(['section-click'])

const mapContainer = ref(null)
const mapInstance = ref(null)
const mapReady = ref(false)
const loadError = ref(false)
const polylines = ref([])      // track所有Polyline
const trafficData = ref({})    // section_id → {vehicle_count, avg_speed, occupancy}
let refreshTimer = null

const AMAP_KEY = import.meta.env.VITE_AMAP_KEY

// ===== 地图加载 =====
const loadAMapScript = () => {
  return new Promise((resolve, reject) => {
    if (window.AMap) return resolve()
    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${AMAP_KEY}&plugin=AMap.Polyline,AMap.InfoWindow`
    script.onload = resolve
    script.onerror = () => reject(new Error('高德地图加载失败'))
    document.head.appendChild(script)
  })
}

// ===== 绘制路网 =====
const drawRoadNetwork = () => {
  if (!mapInstance.value) return
  // 清除旧线
  polylines.value.forEach(p => mapInstance.value.remove(p))
  polylines.value = []

  ROAD_SEGMENTS.forEach(seg => {
    const polyline = new AMap.Polyline({
      path: seg.path,
      strokeColor: '#444444',    // 默认灰色
      strokeWeight: 4,
      strokeOpacity: 0.5,
      lineJoin: 'round',
      lineCap: 'round',
      zIndex: 10,
      extData: { sectionId: seg.id, sectionName: seg.name },
    })
    // 点击事件
    polyline.on('click', (e) => {
      const sid = e.target.getExtData().sectionId
      const sname = e.target.getExtData().sectionName
      const td = trafficData.value[sid]
      emit('section-click', { id: sid, name: sname, ...td })
    })
    mapInstance.value.add(polyline)
    polylines.value.push(polyline)
  })
}

// ===== 更新路况颜色 =====
const updateTrafficColors = () => {
  if (!mapInstance.value || polylines.value.length === 0) return
  polylines.value.forEach(p => {
    const sid = p.getExtData().sectionId
    const td = trafficData.value[sid]
    const occ = td?.occupancy
    p.setOptions({
      strokeColor: getCongestionColor(occ),
      strokeWeight: getCongestionWidth(occ),
      strokeOpacity: getCongestionOpacity(occ),
    })
  })
}

// ===== 获取实时路况数据 =====
const fetchTrafficData = async () => {
  try {
    const res = await trafficApi.getCurrent()
    const items = res.data?.items || res?.items || res.data
    if (Array.isArray(items)) {
      const map = {}
      items.forEach(item => { map[item.section_id] = item })
      trafficData.value = map
      updateTrafficColors()
    }
  } catch (e) {
    // 静默失败，路况数据暂不可用
  }
}

// ===== 生命周期 =====
onMounted(async () => {
  try {
    await loadAMapScript()
    mapInstance.value = new AMap.Map(mapContainer.value, {
      zoom: 14,
      center: [116.4603, 39.9084],  // 国贸CBD真实路网中心 (东大桥路~西大望路 / 通惠河~光华北路)
      mapStyle: 'amap://styles/darkblue',
      resizeEnable: true,
    })
    mapReady.value = true
    drawRoadNetwork()
    await fetchTrafficData()
    refreshTimer = setInterval(fetchTrafficData, 5000)  // 5秒刷新
  } catch (err) {
    console.warn('[TrafficMap]', err.message)
    loadError.value = true
  }
})

onUnmounted(() => {
  clearInterval(refreshTimer)
  mapInstance.value?.destroy()
  mapInstance.value = null
})

// props.sections变化时重新获取路况
watch(() => props.sections, () => {
  if (mapReady.value) fetchTrafficData()
}, { deep: true })
</script>

<style scoped>
.map-overlay {
  display: flex; align-items: center; justify-content: center;
  height: 100%; color: var(--text-secondary);
  background: var(--bg-panel);
}
.map-legend {
  position: absolute; bottom: 12px; left: 12px; z-index: 100;
  background: rgba(0,0,0,.75); border-radius: 8px; padding: 8px 14px;
  display: flex; gap: 16px; flex-wrap: wrap;
  font-size: 12px; color: #ddd;
  pointer-events: none;
}
.legend-item { display: flex; align-items: center; gap: 6px; }
.dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
</style>
