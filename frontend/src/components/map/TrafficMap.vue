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
  routePath: { type: Array, default: () => [] },  // 规划路径 [{name, path:[[lng,lat],...]}]
})
const emit = defineEmits(['section-click', 'map-click'])

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
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${AMAP_KEY}&plugin=AMap.Polyline,AMap.InfoWindow,AMap.Marker`
    script.onload = resolve
    script.onerror = () => reject(new Error('高德地图加载失败'))
    document.head.appendChild(script)
  })
}

// ===== Amap状态→颜色 =====
const amapStatusColor = (status) => {
  // 高德status: 0=未知 1=畅通 2=缓行 3=拥堵 4=严重拥堵
  const map = { 1: '#52c41a', 2: '#fadb14', 3: '#fa8c16', 4: '#f5222d' }
  return map[status] || '#4488aa'  // 未知用蓝色
}

// ===== 绘制路网 (用Amap实时路况作为初始颜色) =====
const drawRoadNetwork = () => {
  if (!mapInstance.value) return
  polylines.value.forEach(p => mapInstance.value.remove(p))
  polylines.value = []

  ROAD_SEGMENTS.forEach(seg => {
    // 用Amap返回的status作为初始颜色（已有实时路况数据）
    const strokeColor = amapStatusColor(seg.status)
    const polyline = new AMap.Polyline({
      path: seg.path,
      strokeColor: strokeColor,
      strokeWeight: 5,
      strokeOpacity: 0.65,
      lineJoin: 'round',
      lineCap: 'round',
      zIndex: 10,
      extData: { sectionName: seg.name },
    })
    polyline.on('click', (e) => {
      const sname = e.target.getExtData().sectionName
      const td = trafficData.value[sname]
      emit('section-click', { id: seg.id, name: sname, speed: seg.speed, status: seg.status, ...td })
    })
    mapInstance.value.add(polyline)
    polylines.value.push(polyline)
  })
}

// ===== 更新路况颜色 =====
const updateTrafficColors = () => {
  if (!mapInstance.value || polylines.value.length === 0) return
  polylines.value.forEach(p => {
    const sname = p.getExtData().sectionName
    const td = trafficData.value[sname]  // 按道路名匹配
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
      // 按道路名建立映射 (section_name → traffic_data)
      items.forEach(item => {
        const name = item.section_name || item.name || ''
        if (name) map[name] = item
      })
      trafficData.value = map
      updateTrafficColors()
    }
  } catch (e) {
    // 静默失败
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
    // 地图点击事件 — 用于应急调度等场景的地图选点
    mapInstance.value.on('click', (e) => {
      emit('map-click', { lng: e.lnglat.getLng(), lat: e.lnglat.getLat() })
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

// ===== 高亮规划路线（每个路段独立绘制，沿实际道路） =====
let routePolylines = []
let routeMarkers = []

const clearRoute = () => {
  routePolylines.forEach(p => mapInstance.value?.remove(p))
  routePolylines = []
  routeMarkers.forEach(m => mapInstance.value?.remove(m))
  routeMarkers = []
}

const highlightRoute = (segments) => {
  if (!mapInstance.value || !segments || !segments.length) return
  clearRoute()

  // 支持格式:
  // 1) route_segments: [{seg_id, name, path: [[lng,lat],...], length_km}, ...] (新，推荐)
  // 2) full_coordinates: [[lng,lat], ...] (旧，单条连续线)
  // 3) 带path字段的对象数组: [{name, path: [[lng,lat],...]}, ...] (旧)

  let segList = []

  if (Array.isArray(segments[0])) {
    // 格式2: 纯坐标数组 → 当作一个路段处理
    segList = [{ path: segments, name: '' }]
  } else {
    segList = segments
  }

  // 所有路段等亮绘制，沿实际道路，路径连续不断开
  segList.forEach((seg) => {
    const segPath = seg.path || seg.coordinates || []
    if (segPath.length < 2) return

    const polyline = new AMap.Polyline({
      path: segPath,
      strokeColor: '#00d4ff',
      strokeWeight: 6,
      strokeOpacity: 0.85,
      lineJoin: 'round',
      lineCap: 'round',
      zIndex: 100,
    })
    mapInstance.value.add(polyline)
    routePolylines.push(polyline)
  })

  if (routePolylines.length === 0) return

  // 起终点标记：取第一个路段起点和最后一个路段终点
  let allPaths = segList.filter(s => (s.path || s.coordinates || []).length >= 2)
  if (allPaths.length === 0) return

  const firstPath = allPaths[0].path || allPaths[0].coordinates
  const lastPath = allPaths[allPaths.length - 1].path || allPaths[allPaths.length - 1].coordinates
  const start = firstPath[0]
  const end = lastPath[lastPath.length - 1]

  if (window.AMap?.Marker) {
    const startM = new AMap.Marker({
      position: start,
      content: '<div style="background:#00d4ff;color:#000;padding:2px 6px;border-radius:4px;font-size:12px;font-weight:bold">起</div>',
      offset: new AMap.Pixel(-12, -12),
      zIndex: 101,
    })
    const endM = new AMap.Marker({
      position: end,
      content: '<div style="background:#ff4d4f;color:#fff;padding:2px 6px;border-radius:4px;font-size:12px;font-weight:bold">终</div>',
      offset: new AMap.Pixel(-12, -12),
      zIndex: 101,
    })
    mapInstance.value.add([startM, endM])
    routeMarkers = [startM, endM]
  }

  // 自适应视野（适配所有路段）
  mapInstance.value.setFitView(routePolylines)
}

watch(() => props.routePath, (val) => {
  if (mapReady.value && val) highlightRoute(val)
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
