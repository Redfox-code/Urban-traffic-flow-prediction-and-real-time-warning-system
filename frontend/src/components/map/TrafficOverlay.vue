<template>
  <div class="traffic-overlay">
    <!-- 图例 -->
    <div class="to-legend">
      <div class="to-legend-item">
        <span class="to-dot" style="background:var(--traffic-smooth)"></span>畅通 &lt;30%
      </div>
      <div class="to-legend-item">
        <span class="to-dot" style="background:var(--traffic-slow)"></span>缓行 &lt;60%
      </div>
      <div class="to-legend-item">
        <span class="to-dot" style="background:var(--traffic-congested)"></span>拥堵 &lt;85%
      </div>
      <div class="to-legend-item">
        <span class="to-dot" style="background:var(--traffic-jammed)"></span>严重 ≥85%
      </div>
      <div class="to-source-tag">
        <el-tag size="small" :type="dataSource === 'amap' ? 'success' : 'warning'" effect="dark">
          {{ dataSource === 'amap' ? '📡 高德实时' : '🎲 模拟' }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { getCongestionColor, getCongestionWidth, getCongestionOpacity } from '@/data/roadNetwork'
import { useTrafficStore } from '@/store/traffic'
import { trafficApi } from '@/api/traffic'

const props = defineProps({
  map: { type: Object, required: true },
  sections: { type: Array, default: () => [] },
  autoRefresh: { type: Boolean, default: true },
  refreshInterval: { type: Number, default: 30000 },
})

const dataSource = ref('mock')
const polylines = ref([])
const trafficStore = useTrafficStore()
let refreshTimer = null

// 用高德status颜色初始化
const amapStatusColor = (status) => {
  const map = { 1: '#52c41a', 2: '#fadb14', 3: '#fa8c16', 4: '#f5222d' }
  return map[status] || '#4488aa'
}

// 绘制路段集合
const drawSections = (segments, trafficMap) => {
  if (!props.map) return
  clearPolylines()

  segments.forEach(seg => {
    const occ = trafficMap?.[seg.name]?.occupancy ?? (seg.occupancy ?? -1)
    const polyline = new AMap.Polyline({
      path: seg.path,
      strokeColor: occ >= 0 ? getCongestionColor(occ) : amapStatusColor(seg.status),
      strokeWeight: occ >= 0 ? getCongestionWidth(occ) : 5,
      strokeOpacity: occ >= 0 ? getCongestionOpacity(occ) : 0.65,
      lineJoin: 'round',
      lineCap: 'round',
      zIndex: 10,
      extData: { sectionName: seg.name, id: seg.id },
    })
    polyline.on('click', (e) => {
      const ed = e.target.getExtData()
      const td = trafficMap?.[ed.sectionName]
      props.map.emit('section-click', {
        id: ed.id, name: ed.sectionName,
        ...td,
      })
    })
    props.map.add(polyline)
    polylines.value.push(polyline)
  })
}

const clearPolylines = () => {
  polylines.value.forEach(p => props.map?.remove(p))
  polylines.value = []
}

// 增量更新颜色（WebSocket推送后用）
const updateColors = (trafficMap) => {
  polylines.value.forEach(p => {
    const ed = p.getExtData()
    const td = trafficMap?.[ed.sectionName]
    if (td) {
      p.setOptions({
        strokeColor: getCongestionColor(td.occupancy),
        strokeWeight: getCongestionWidth(td.occupancy),
        strokeOpacity: getCongestionOpacity(td.occupancy),
      })
    }
  })
}

const fetchData = async () => {
  try {
    const res = await trafficApi.getCurrent()
    const items = res.data?.items || res?.items || res.data
    if (Array.isArray(items)) {
      const map = {}
      items.forEach(item => {
        const name = item.section_name || item.name || ''
        if (name) map[name] = item
      })
      if (items.length > 0) dataSource.value = items[0].source || 'mock'
      updateColors(map)
      trafficStore.updateRealtime(map)
    }
  } catch { /* silent */ }
}

// 监听外部数据变化（WebSocket触发）
watch(() => trafficStore.realtimeData, (val) => {
  if (val && Object.keys(val).length > 0) updateColors(val)
}, { deep: true })

onMounted(() => {
  if (props.sections.length > 0) {
    drawSections(props.sections)
  }
  if (props.autoRefresh) {
    refreshTimer = setInterval(fetchData, props.refreshInterval)
  }
})

onUnmounted(() => {
  clearInterval(refreshTimer)
  clearPolylines()
})

// sections动态更新
watch(() => props.sections, (val) => {
  if (val.length > 0) drawSections(val)
}, { deep: true })

defineExpose({ drawSections, updateColors, clearPolylines })
</script>

<style scoped>
.traffic-overlay { position: absolute; top: 0; left: 0; right: 0; bottom: 0; pointer-events: none; z-index: 0; }
.to-legend {
  position: absolute; bottom: 12px; left: 12px; z-index: 100;
  background: rgba(0,0,0,.75); border-radius: 8px; padding: 8px 14px;
  display: flex; gap: 14px; flex-wrap: wrap; align-items: center;
  font-size: 12px; color: #ddd; pointer-events: auto;
}
.to-legend-item { display: flex; align-items: center; gap: 6px; }
.to-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.to-source-tag { margin-left: 4px; }
</style>
