<template>
  <div class="route-plan-view">
    <!-- 响应式容器: mobile纵向, desktop横向 -->
    <div class="rpv-container" :class="{ 'is-desktop': !isMobile }">
      <!-- 地图区 -->
      <div class="rpv-map-section" :style="isMobile ? 'height:55vh;min-height:280px' : 'flex:1.2'">
        <!-- 地图组件(独立AMap实例 + POI搜索 + GPS + 长按选点) -->
        <RoutePlanMap
          ref="mapRef"
          :height="isMobile ? '55vh' : '100%'"
          :standalone="true"
          mode="start-end"
          :routeData="result"
          @point-select="onMapPointSelect"
          @poi-select="onMapPOISelect"
        />
        <!-- GPS手动定位按钮(地图组件自带一个,此处补充大按钮) -->
        <div class="rpv-gps-big" @click="locateGPS" title="GPS定位">
          <span class="rpv-gps-icon">📍</span>
          <span class="rpv-gps-text">定位当前位置</span>
        </div>
      </div>

      <!-- 面板区 -->
      <div class="rpv-panel-section">
        <div class="rpv-panel-scroll">
          <!-- 表单卡片 -->
          <el-card shadow="never" class="rpv-card">
            <div class="rpv-form">
              <!-- 起点 -->
              <div class="rpv-field">
                <div class="rpv-field-label">
                  <span class="rpv-dot origin-dot"></span> 起点
                  <el-button text size="small" class="rpv-gps-btn" @click="locateGPS" :disabled="gpsLoading">
                    {{ gpsLoading ? '定位中...' : '📍 自动定位' }}
                  </el-button>
                </div>
                <el-select v-model="origin" filterable remote :remote-method="searchSections"
                  placeholder="搜索起点路段" style="width:100%" @change="onOriginChange">
                  <el-option v-for="s in sectionOptions" :key="s.id" :label="s.name" :value="s.id" />
                </el-select>
              </div>

              <!-- 交换 + 地图选点 -->
              <div class="rpv-swap-row">
                <el-button circle size="small" @click="swapPoints" :disabled="!origin && !dest" title="交换起终点">
                  ⇅
                </el-button>
                <span class="rpv-hint" v-if="!origin && !dest">👇 在地图长按选点或搜索POI</span>
                <span class="rpv-hint" v-else-if="!origin">← 长按地图选起点</span>
                <span class="rpv-hint" v-else-if="!dest">→ 长按地图选终点</span>
                <span class="rpv-hint" v-else>完成选择，点击下方规划</span>
              </div>

              <!-- 终点 -->
              <div class="rpv-field">
                <div class="rpv-field-label">
                  <span class="rpv-dot dest-dot"></span> 终点
                </div>
                <el-select v-model="dest" filterable remote :remote-method="searchSections"
                  placeholder="搜索终点路段" style="width:100%" @change="onDestChange">
                  <el-option v-for="s in sectionOptions" :key="s.id" :label="s.name" :value="s.id" />
                </el-select>
              </div>

              <!-- 出发时间 -->
              <div class="rpv-depart-row">
                <div class="rpv-field-label">🕐 出发时间</div>
                <el-radio-group v-model="departMode" size="small">
                  <el-radio-button value="now">现在出发</el-radio-button>
                  <el-radio-button value="scheduled">指定时间</el-radio-button>
                </el-radio-group>
                <el-date-picker v-if="departMode === 'scheduled'"
                  v-model="scheduledTime" type="datetime"
                  placeholder="选择出发时间" style="width:100%;margin-top:8px"
                  :disabled-date="disablePastDate"
                  value-format="YYYY-MM-DD HH:mm:ss"
                  size="small" />
              </div>

              <!-- 规划按钮 -->
              <el-button type="primary" class="rpv-plan-btn" @click="planRoute"
                :loading="loading" :disabled="!origin || !dest">
                <span v-if="!loading">🚘 规划路径</span>
                <span v-else>规划中...</span>
              </el-button>

              <!-- 错误提示 -->
              <el-alert v-if="errorMsg" :title="errorMsg" type="error" show-icon
                :closable="true" @close="errorMsg = ''" class="rpv-error" />
            </div>
          </el-card>

          <!-- 结果卡片 -->
          <template v-if="result">
            <!-- 路线摘要 -->
            <el-card shadow="never" class="rpv-card rpv-result-summary">
              <template #header>
                <div class="rpv-result-header">
                  <span>📍 推荐路线</span>
                  <el-tag size="small" :type="congestionType" effect="dark">
                    {{ congestionLabel }}
                  </el-tag>
                </div>
              </template>
              <div class="rpv-stats-row">
                <div class="rpv-stat-item">
                  <div class="rpv-stat-val">{{ result.total_distance }} <small>km</small></div>
                  <div class="rpv-stat-lbl">总距离</div>
                </div>
                <div class="rpv-stat-item">
                  <div class="rpv-stat-val">{{ result.estimated_time }} <small>min</small></div>
                  <div class="rpv-stat-lbl">预计时间</div>
                </div>
                <div class="rpv-stat-item">
                  <div class="rpv-stat-val">{{ result.path?.length || 0 }}</div>
                  <div class="rpv-stat-lbl">途经路段</div>
                </div>
              </div>
            </el-card>

            <!-- 途经路段详情 -->
            <el-card shadow="never" class="rpv-card">
              <template #header>
                <span style="font-weight:bold;color:var(--text-primary)">🛣️ 途经路段详情</span>
              </template>
              <div v-for="(seg, i) in result.path" :key="i" class="rpv-segment">
                <div class="rpv-seg-num">{{ i + 1 }}</div>
                <div class="rpv-seg-info">
                  <div class="rpv-seg-name">{{ seg.name }}</div>
                  <div class="rpv-seg-sub">
                    <span>{{ seg.length }} km</span>
                    <span v-if="seg.avg_speed != null && seg.avg_speed > 0" style="margin-left:8px">
                      🚗 {{ seg.avg_speed }} km/h
                    </span>
                    <span v-if="seg.occupancy != null" style="margin-left:4px">
                      <el-tag size="small" :type="occType(seg.occupancy)" effect="dark">
                        {{ occLabel(seg.occupancy) }}
                      </el-tag>
                    </span>
                    <span v-else style="margin-left:4px">
                      <el-tag size="small" type="info" effect="plain">无实时数据</el-tag>
                    </span>
                  </div>
                </div>
              </div>
            </el-card>

            <!-- 底部操作栏 -->
            <div class="rpv-actions">
              <el-button type="primary" class="rpv-action-btn" @click="saveAsFavorite"
                :loading="saving" :disabled="!userStore.isLoggedIn">
                {{ userStore.isLoggedIn ? '⭐ 保存为常用路线' : '登录后保存常用路线' }}
              </el-button>
              <el-button class="rpv-action-btn rpv-nav-btn" @click="startNavigation">
                🧭 开始导航
              </el-button>
            </div>
          </template>

          <!-- 空状态 -->
          <el-empty v-if="!result && !loading && !errorMsg && origin && dest"
            description="点击「规划路径」获取路线" :image-size="80" />

          <!-- 未选择起终点提示 -->
          <el-empty v-if="!result && !loading && !origin && !dest"
            description="在地图长按选点，或搜索起终点路段" :image-size="80" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { routeApi } from '@/api/routePlan'
import { sectionsApi } from '@/api/sections'
import { travelerApi } from '@/api/traveler'
import { ElMessage, ElMessageBox } from 'element-plus'
import RoutePlanMap from '@/components/map/RoutePlanMap.vue'

const router = useRouter()
const userStore = useUserStore()

// ===== 响应式布局 =====
const isMobile = ref(window.innerWidth < 768)
function checkWidth() { isMobile.value = window.innerWidth < 768 }
window.addEventListener('resize', checkWidth)
onUnmounted(() => window.removeEventListener('resize', checkWidth))

// ===== 状态 =====
const sections = ref([])
const sectionOptions = ref([])
const origin = ref(null)
const dest = ref(null)
const loading = ref(false)
const saving = ref(false)
const errorMsg = ref('')
const result = ref(null)
const gpsLoading = ref(false)
const departMode = ref('now')
const scheduledTime = ref('')

const mapRef = ref(null)

// ===== 加载路段列表 =====
onMounted(async () => {
  try {
    const res = await sectionsApi.getList()
    sections.value = res.data?.items || res?.items || []
    sectionOptions.value = sections.value
  } catch (e) {
    console.warn('加载路段列表失败', e)
  }
})

// ===== 路段搜索 =====
function searchSections(query) {
  if (!query) {
    sectionOptions.value = sections.value
    return
  }
  const q = query.toLowerCase()
  sectionOptions.value = sections.value.filter(
    s => s.name?.toLowerCase().includes(q)
  )
}

// ===== 交换起终点 =====
function swapPoints() {
  const tmp = origin.value
  origin.value = dest.value
  dest.value = tmp
  // 重新规划
  if (origin.value && dest.value) planRoute()
}

// ===== GPS定位 =====
function locateGPS() {
  if (!navigator.geolocation) {
    ElMessage.warning('当前浏览器不支持GPS定位')
    return
  }
  gpsLoading.value = true
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      gpsLoading.value = false
      const { latitude, longitude } = pos.coords
      // 在地图上定位
      if (mapRef.value?.locateMe) {
        mapRef.value.locateMe()
      }
      ElMessage.success(`已定位到当前位置 [${longitude.toFixed(4)}, ${latitude.toFixed(4)}]`)
      // 尝试匹配最近路段作为起点
      autoMatchNearestSection(longitude, latitude, 'origin')
    },
    () => {
      gpsLoading.value = false
      ElMessage.error('GPS定位失败，请检查位置权限')
    },
    { enableHighAccuracy: true, timeout: 10000 }
  )
}

/** 根据坐标自动匹配最近路段 */
function autoMatchNearestSection(lng, lat, target) {
  let best = null, bestDist = Infinity
  for (const s of sections.value) {
    const coords = s.coordinates
    if (!coords) continue
    const pts = coords.waypoints || coords.path || []
    for (const pt of pts) {
      const d = Math.sqrt((pt[0] - lng) ** 2 + (pt[1] - lat) ** 2)
      if (d < bestDist) { bestDist = d; best = s }
    }
  }
  if (best && bestDist < 0.01) {
    if (target === 'origin') origin.value = best.id
    else dest.value = best.id
  }
}

// ===== 地图选点 =====
function onMapPointSelect(data) {
  if (!data || !data.lng) return
  // 通过坐标匹配最近路段
  autoMatchNearestSection(data.lng, data.lat,
    !origin.value ? 'origin' : dest.value ? 'origin' : 'dest')
  // 如果起终点都已填，检查唯一性后重新规划
  if (origin.value && dest.value) planRoute()
}

function onMapPOISelect(poi) {
  if (!poi || !poi.location) return
  autoMatchNearestSection(poi.location.lng, poi.location.lat,
    !origin.value ? 'origin' : 'dest')
}

// ===== 起终点变化 =====
function onOriginChange() { if (origin.value && dest.value) planRoute() }
function onDestChange() { if (origin.value && dest.value) planRoute() }

// ===== 时间选择 =====
function disablePastDate(time) {
  return time.getTime() < Date.now() - 86400000
}

// ===== 路径规划 =====
async function planRoute() {
  if (!origin.value || !dest.value) {
    errorMsg.value = '请选择起点和终点路段'
    return
  }
  if (origin.value === dest.value) {
    errorMsg.value = '起点和终点不能相同'
    return
  }
  errorMsg.value = ''
  loading.value = true
  result.value = null
  try {
    const payload = {
      origin_section_id: origin.value,
      dest_section_id: dest.value,
    }
    if (departMode.value === 'scheduled' && scheduledTime.value) {
      payload.depart_time = scheduledTime.value
    }
    const res = await routeApi.plan(payload)
    const data = res.data || res
    if (!data || !data.path) {
      errorMsg.value = '规划失败，请尝试其他路段组合'
      return
    }
    result.value = data
  } catch (e) {
    const msg = e?.response?.data?.message || e?.message || '网络请求失败'
    errorMsg.value = msg
  } finally {
    loading.value = false
  }
}

// ===== 拥堵度计算 =====
const congestionGrade = computed(() => {
  if (!result.value?.path?.length) return 0
  const occs = result.value.path.map(s => s.occupancy || 0).filter(v => v > 0)
  if (!occs.length) return 0
  const avg = occs.reduce((a, b) => a + b, 0) / occs.length
  return avg
})
const congestionType = computed(() => {
  const g = congestionGrade.value
  if (g < 30) return 'success'
  if (g < 60) return 'warning'
  if (g < 85) return 'danger'
  return 'danger'
})
const congestionLabel = computed(() => {
  const g = congestionGrade.value
  if (!g) return '暂无路况'
  if (g < 30) return '🟢 畅通'
  if (g < 60) return '🟡 缓行'
  if (g < 85) return '🟠 拥堵'
  return '🔴 严重拥堵'
})

function occType(occ) {
  if (occ == null) return 'info'
  if (occ < 30) return 'success'
  if (occ < 60) return 'warning'
  return 'danger'
}
function occLabel(occ) {
  if (occ == null) return '无数据'
  if (occ < 30) return '畅通'
  if (occ < 60) return '缓行'
  if (occ < 85) return '拥堵'
  return '严重'
}

// ===== 保存为常用路线 =====
async function saveAsFavorite() {
  if (!userStore.isLoggedIn) {
    ElMessageBox.confirm('登录后可保存常用路线，是否前往登录？', '提示', {
      confirmButtonText: '去登录', cancelButtonText: '取消', type: 'info',
    }).then(() => router.push({ name: 'Login', query: { redirect: '/traveler/my-trips' } }))
      .catch(() => {})
    return
  }
  if (!result.value) return
  saving.value = true
  try {
    // 查找起终点名称
    const o = sections.value.find(s => s.id === origin.value)
    const d = sections.value.find(s => s.id === dest.value)
    await travelerApi.saveRoute({
      origin_name: o?.name || '',
      dest_name: d?.name || '',
      depart_time: scheduledTime.value || new Date().toISOString(),
    })
    ElMessage.success('已保存到常用路线')
  } catch (e) {
    ElMessage.error('保存失败: ' + (e?.response?.data?.message || e?.message))
  } finally {
    saving.value = false
  }
}

// ===== 开始导航（占位） =====
function startNavigation() {
  if (!result.value) return
  ElMessage.success('导航功能即将上线 🚀')
}
</script>

<style scoped>
.route-plan-view {
  height: 100%;
  overflow: hidden;
}
.rpv-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 12px;
}
.rpv-container.is-desktop {
  flex-direction: row;
}
.rpv-map-section {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  min-height: 280px;
  flex-shrink: 0;
}
.rpv-gps-big {
  position: absolute;
  bottom: 16px;
  left: 12px;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--bg-panel);
  border: 1px solid rgba(255,255,255,.15);
  border-radius: 20px;
  cursor: pointer;
  color: var(--accent-blue);
  font-size: 12px;
  transition: background .2s;
  backdrop-filter: blur(4px);
}
.rpv-gps-big:hover { background: rgba(0,212,255,.15); }
.rpv-gps-icon { font-size: 16px; }
.rpv-panel-section {
  flex: 1;
  overflow: hidden;
  min-height: 0;
}
.rpv-panel-scroll {
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-right: 4px;
}
.rpv-card {
  flex-shrink: 0;
}
.rpv-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.rpv-field-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.rpv-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.origin-dot { background: #00e676; }
.dest-dot { background: #f44336; }
.rpv-gps-btn {
  margin-left: auto;
  font-size: 12px;
  color: var(--accent-blue);
}
.rpv-swap-row {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
  padding: 4px 0;
}
.rpv-hint {
  font-size: 12px;
  color: var(--text-secondary);
  font-style: italic;
}
.rpv-depart-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.rpv-plan-btn {
  width: 100%;
  margin-top: 4px;
}
.rpv-error {
  margin-top: 4px;
}
/* 结果 */
.rpv-result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: bold;
  color: var(--text-primary);
}
.rpv-stats-row {
  display: flex;
  gap: 12px;
}
.rpv-stat-item {
  flex: 1;
  text-align: center;
  padding: 12px 8px;
  background: rgba(0,212,255,.06);
  border-radius: 8px;
}
.rpv-stat-val {
  font-size: 22px;
  font-weight: bold;
  color: var(--accent-blue);
}
.rpv-stat-val small { font-size: 13px; font-weight: normal; }
.rpv-stat-lbl {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}
/* 路段详情 */
.rpv-segment {
  display: flex;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255,255,255,.04);
  align-items: flex-start;
}
.rpv-segment:last-child { border-bottom: none; }
.rpv-seg-num {
  width: 24px; height: 24px;
  background: rgba(0,212,255,.15);
  color: var(--accent-blue);
  border-radius: 50%;
  text-align: center;
  line-height: 24px;
  font-size: 12px;
  font-weight: bold;
  flex-shrink: 0;
}
.rpv-seg-info { flex: 1; }
.rpv-seg-name { font-size: 14px; font-weight: 500; color: var(--text-primary); }
.rpv-seg-sub { font-size: 12px; color: var(--text-secondary); margin-top: 2px; display: flex; flex-wrap: wrap; align-items: center; }
/* 底部操作栏 */
.rpv-actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
  padding: 4px 0;
}
.rpv-action-btn {
  flex: 1;
}
.rpv-nav-btn {
  background: rgba(0,212,255,.12);
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}
.rpv-nav-btn:hover { background: rgba(0,212,255,.25); }
</style>
