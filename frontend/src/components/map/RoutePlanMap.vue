<template>
  <div class="route-plan-map">
    <!-- 搜索栏 -->
    <div class="rpm-search">
      <el-input
        v-model="searchQuery"
        placeholder="搜索POI（如：国贸大厦）"
        size="small"
        clearable
        @input="onSearchInput"
        @clear="clearSearchResults"
      >
        <template #prefix><el-icon :size="14"><Search /></el-icon></template>
      </el-input>
      <div v-if="searchResults.length > 0" class="rpm-search-results">
        <div v-for="(poi, i) in searchResults" :key="i" class="rpm-search-item" @click="selectPOI(poi)">
          <div class="rpm-poi-name">{{ poi.name }}</div>
          <div class="rpm-poi-addr">{{ poi.address || poi.pname + poi.cityname }}</div>
        </div>
      </div>
    </div>

    <!-- 地图容器 -->
    <div ref="mapContainer" class="rpm-map"></div>

    <!-- GPS定位按钮 -->
    <div class="rpm-gps-btn" @click="locateMe">
      <el-icon :size="18"><Location /></el-icon>
    </div>

    <!-- 长按提示 -->
    <div v-if="showLongPressHint" class="rpm-hint">长按地图选点</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Search, Location } from '@element-plus/icons-vue'

const emit = defineEmits(['start-select', 'end-select', 'point-select', 'poi-select'])

const props = defineProps({
  map: { type: Object, default: null },
  standalone: { type: Boolean, default: true }, // 独立模式（自带地图实例）
  height: { type: String, default: '400px' },
  mode: { type: String, default: 'start-end' }, // 'start-end' | 'single-point'
})

const mapContainer = ref(null)
const mapInstance = ref(null)
const mapReady = ref(false)
const searchQuery = ref('')
const searchResults = ref([])
const showLongPressHint = ref(false)

let gpsMarker = null
let longPressTimer = null
let selectedMarkers = []

const AMAP_KEY = import.meta.env.VITE_AMAP_KEY

const loadAMap = () => {
  return new Promise((resolve, reject) => {
    if (window.AMap) return resolve()
    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${AMAP_KEY}&plugin=AMap.Polyline,AMap.Marker,AMap.AutoComplete,AMap.PlaceSearch,AMap.Geolocation`
    script.onload = resolve
    script.onerror = reject
    document.head.appendChild(script)
  })
}

const initMap = async () => {
  if (props.map) {
    mapInstance.value = props.map
    mapReady.value = true
    return
  }
  try {
    await loadAMap()
    mapInstance.value = new AMap.Map(mapContainer.value, {
      zoom: 14,
      center: [116.4603, 39.9084],
      mapStyle: 'amap://styles/darkblue',
      resizeEnable: true,
    })
    mapReady.value = true
    bindEvents()
  } catch (e) {
    console.warn('[RoutePlanMap] 地图加载失败:', e)
  }
}

const bindEvents = () => {
  if (!mapInstance.value) return

  // 长按选点
  mapInstance.value.on('mousedown', (e) => {
    longPressTimer = setTimeout(() => {
      showLongPressHint.value = true
      const lnglat = e.lnglat
      if (lnglat) selectPoint([lnglat.lng, lnglat.lat])
      setTimeout(() => { showLongPressHint.value = false }, 2000)
    }, 600)
  })
  mapInstance.value.on('mouseup', () => {
    clearTimeout(longPressTimer)
  })

  // 点击选点（single-point模式）
  if (props.mode === 'single-point') {
    mapInstance.value.on('click', (e) => {
      if (e.lnglat) selectPoint([e.lnglat.lng, e.lnglat.lat])
    })
  }
}

// GPS定位
const locateMe = () => {
  if (!mapInstance.value || !window.AMap) return
  const geolocation = new AMap.Geolocation({
    enableHighAccuracy: true,
    timeout: 10000,
  })
  geolocation.getCurrentPosition((status, result) => {
    if (status === 'complete') {
      const pos = [result.position.lng, result.position.lat]
      mapInstance.value.setCenter(pos)
      mapInstance.value.setZoom(15)

      if (gpsMarker) mapInstance.value.remove(gpsMarker)
      gpsMarker = new AMap.Marker({
        position: pos,
        content: '<div class="rpm-gps-dot"><div class="rpm-gps-pulse"></div></div>',
        offset: new AMap.Pixel(-12, -12),
        zIndex: 200,
      })
      mapInstance.value.add(gpsMarker)
      emit('point-select', { type: 'gps', lng: pos[0], lat: pos[1] })
    }
  })
}

// 选择点
const selectPoint = (lnglat) => {
  if (!mapInstance.value || !window.AMap) return
  const marker = new AMap.Marker({
    position: lnglat,
    content: `<div class="rpm-point-marker">📍</div>`,
    offset: new AMap.Pixel(-16, -16),
    zIndex: 100,
  })
  mapInstance.value.add(marker)
  selectedMarkers.push(marker)
  emit('point-select', { lng: lnglat[0], lat: lnglat[1] })
}

// POI搜索
const onSearchInput = async (query) => {
  if (!query || query.length < 2) { searchResults.value = []; return }
  try {
    const { status, result } = await new Promise((resolve) => {
      const placeSearch = new AMap.PlaceSearch({
        type: '交通设施|商务大厦|购物|生活服务',
        city: '北京',
        pageSize: 6,
      })
      placeSearch.search(query, (s, r) => resolve({ status: s, result: r }))
    })
    if (status === 'complete' && result.poiList) {
      searchResults.value = result.poiList.pois || []
    }
  } catch { /* silent */ }
}

const clearSearchResults = () => { searchResults.value = [] }

const selectPOI = (poi) => {
  const pos = [poi.location.lng, poi.location.lat]
  mapInstance.value?.setCenter(pos)
  mapInstance.value?.setZoom(16)
  selectPoint(pos)
  searchQuery.value = poi.name
  searchResults.value = []
  emit('poi-select', poi)
}

const clearMarkers = () => {
  selectedMarkers.forEach(m => mapInstance.value?.remove(m))
  selectedMarkers = []
  if (gpsMarker) { mapInstance.value?.remove(gpsMarker); gpsMarker = null }
}

onMounted(initMap)

onUnmounted(() => {
  clearMarkers()
  if (props.standalone && mapInstance.value) {
    mapInstance.value.destroy()
  }
})

defineExpose({ locateMe, clearMarkers, selectPoint, mapInstance })
</script>

<style scoped>
.route-plan-map {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
}
.rpm-search {
  position: absolute;
  top: 12px;
  left: 12px;
  right: 60px;
  z-index: 100;
}
.rpm-search-results {
  background: var(--bg-panel);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 8px;
  max-height: 200px;
  overflow-y: auto;
  margin-top: 4px;
}
.rpm-search-item {
  padding: 8px 12px;
  cursor: pointer;
  border-bottom: 1px solid rgba(255,255,255,.04);
  transition: background .2s;
}
.rpm-search-item:hover { background: rgba(0,212,255,.08); }
.rpm-poi-name { font-size: 13px; color: var(--text-primary); }
.rpm-poi-addr { font-size: 11px; color: var(--text-secondary); margin-top: 2px; }
.rpm-map {
  width: 100%;
  height: v-bind(height);
}
.rpm-gps-btn {
  position: absolute;
  bottom: 16px;
  right: 16px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--bg-panel);
  border: 1px solid rgba(255,255,255,.15);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--accent-blue);
  z-index: 100;
  transition: background .2s;
}
.rpm-gps-btn:hover { background: rgba(0,212,255,.15); }
.rpm-hint {
  position: absolute;
  bottom: 60px;
  left: 50%;
  transform: translateX(-50%);
  padding: 6px 14px;
  background: rgba(0,0,0,.8);
  border-radius: 6px;
  color: #fff;
  font-size: 12px;
  white-space: nowrap;
  z-index: 100;
  animation: rpm-fade 2s ease-in-out;
}
.rpm-point-marker { font-size: 24px; filter: drop-shadow(0 2px 4px rgba(0,0,0,.4)); }
@keyframes rpm-fade { 0% { opacity: 0; } 20% { opacity: 1; } 80% { opacity: 1; } 100% { opacity: 0; } }
</style>

<style>
.rpm-gps-dot {
  width: 24px; height: 24px; border-radius: 50%;
  background: #1890ff; position: relative;
}
.rpm-gps-pulse {
  position: absolute; top: -6px; left: -6px;
  width: 36px; height: 36px; border-radius: 50%;
  background: rgba(24,144,255,.3);
  animation: rpm-pulse 2s infinite;
}
@keyframes rpm-pulse {
  0% { transform: scale(.8); opacity: .6; }
  100% { transform: scale(2); opacity: 0; }
}
</style>
