<template>
  <div class="emergency-view">
    <!-- 左列：规划面板 -->
    <div class="ev-left">
      <!-- 应急路径规划表单 -->
      <el-card shadow="never" class="ev-card">
        <template #header><span class="card-title">🚑 应急路径规划</span></template>
        <el-form label-width="90px" size="default">
          <el-form-item label="车辆类型">
            <el-select v-model="planForm.vehicle_type" placeholder="选择车辆类型" style="width:100%">
              <el-option label="🚑 救护车" value="ambulance" />
              <el-option label="🚒 消防车" value="fire" />
              <el-option label="🚓 警车" value="police" />
            </el-select>
          </el-form-item>
          <!-- 起点选择 -->
          <div class="coord-section" :class="{ 'coord-picking': pickingOrigin }">
            <div class="coord-header">
              🟢 起点
              <el-button size="small" text :type="pickingOrigin ? 'warning' : 'primary'" @click="startPick('origin')" style="margin-left:8px">
                {{ pickingOrigin ? '⏳ 请点击地图...' : '📍 从地图选择' }}
              </el-button>
            </div>
            <div class="coord-display" v-if="planForm.origin.lat != null">
              <span class="coord-val">{{ planForm.origin.lat.toFixed(6) }}, {{ planForm.origin.lng.toFixed(6) }}</span>
              <el-button text size="small" type="danger" @click="clearPoint('origin')">✕</el-button>
            </div>
            <div class="coord-empty" v-else>点击「从地图选择」后在地图上点击起点位置</div>
          </div>
          <!-- 终点选择 -->
          <div class="coord-section" :class="{ 'coord-picking': pickingDest }">
            <div class="coord-header">
              🔴 终点
              <el-button size="small" text :type="pickingDest ? 'warning' : 'danger'" @click="startPick('dest')" style="margin-left:8px">
                {{ pickingDest ? '⏳ 请点击地图...' : '📍 从地图选择' }}
              </el-button>
            </div>
            <div class="coord-display" v-if="planForm.destination.lat != null">
              <span class="coord-val">{{ planForm.destination.lat.toFixed(6) }}, {{ planForm.destination.lng.toFixed(6) }}</span>
              <el-button text size="small" type="danger" @click="clearPoint('dest')">✕</el-button>
            </div>
            <div class="coord-empty" v-else>点击「从地图选择」后在地图上点击终点位置</div>
          </div>
          <el-form-item>
            <el-button type="primary" @click="doPlan" :loading="planLoading" :disabled="!canPlan" style="width:100%">
              🗺️ 规划最优路径
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 规划结果 -->
      <el-card v-if="planResult" shadow="never" class="ev-card result-highlight">
        <template #header><span class="card-title">📊 规划结果</span></template>
        <div class="result-stats">
          <div class="result-stat">
            <div class="rs-val" style="color:#00d4ff">{{ formatSec(planResult.est_travel_time_sec) }}</div>
            <div class="rs-lbl">预计时间</div>
          </div>
          <div class="result-stat">
            <div class="rs-val" style="color:#ff9800">{{ formatSec(planResult.normal_travel_time_sec) }}</div>
            <div class="rs-lbl">常规时间</div>
          </div>
          <div class="result-stat">
            <div class="rs-val" style="color:#4caf50">{{ planResult.time_saved_pct ?? 0 }}%</div>
            <div class="rs-lbl">节省</div>
          </div>
          <div class="result-stat">
            <div class="rs-val" style="color:#2196f3">{{ planResult.green_wave ?? 0 }}</div>
            <div class="rs-lbl">绿波路口</div>
          </div>
        </div>
        <div class="result-detail">
          <div class="detail-row">
            <span class="detail-label">车辆类型</span>
            <span class="detail-value">{{ vehicleLabel(planResult.vehicle_type || planForm.vehicle_type) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">节省时间</span>
            <span class="detail-value" style="color:#4caf50">
              -{{ formatSec(Math.max(0, (planResult.normal_travel_time_sec || 0) - (planResult.est_travel_time_sec || 0))) }}
            </span>
          </div>
        </div>
        <el-button type="success" @click="doCreateRecord" :loading="createLoading" style="width:100%;margin-top:8px">
          ✅ 创建调度记录
        </el-button>
      </el-card>

      <!-- 调度记录 -->
      <el-card shadow="never" class="ev-card">
        <template #header><span class="card-title">📋 调度记录</span></template>
        <el-table :data="records" size="small" style="width:100%" max-height="280" v-loading="recordsLoading">
          <el-table-column prop="vehicle_type" label="车辆" width="80">
            <template #default="{row}">{{ vehicleLabel(row.vehicle_type) }}</template>
          </el-table-column>
          <el-table-column prop="created_at" label="时间" min-width="130">
            <template #default="{row}">{{ formatTimeStr(row.created_at) }}</template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{row}">
              <el-tag size="small" :type="statusType(row.status)" effect="dark">
                {{ statusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{row}">
              <template v-if="row.status === 'active'">
                <el-button type="success" link size="small" @click="updateStatus(row.id, 'completed')">完成</el-button>
                <el-button type="danger" link size="small" @click="updateStatus(row.id, 'cancelled')">取消</el-button>
              </template>
              <span v-else style="color:var(--text-secondary);font-size:12px">—</span>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!recordsLoading && records.length === 0" description="暂无调度记录" :image-size="50" />
        <div v-if="recordsTotal > recordsPageSize" class="ev-pagination">
          <el-pagination
            v-model:current-page="recordsPage"
            :page-size="recordsPageSize"
            :total="recordsTotal"
            layout="total, prev, pager, next"
            size="small"
            @current-change="fetchRecords"
          />
        </div>
      </el-card>
    </div>

    <!-- 右列：地图 -->
    <div class="ev-right">
      <TrafficMap :routePath="routePath" mapHeight="calc(100vh - 88px)" @map-click="onMapClick" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { emergencyApi } from '@/api/emergency'
import TrafficMap from '@/components/map/TrafficMap.vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// ===== 表单数据 =====
const planForm = reactive({
  vehicle_type: 'ambulance',
  origin: { lat: null, lng: null },
  destination: { lat: null, lng: null },
})

const planLoading = ref(false)
const planResult = ref(null)
const createLoading = ref(false)

// 地图选点状态
const pickingOrigin = ref(false)
const pickingDest = ref(false)

// 是否可规划
const canPlan = computed(() => {
  return planForm.origin.lat != null && planForm.origin.lng != null &&
         planForm.destination.lat != null && planForm.destination.lng != null
})

// 地图路线路径
const routePath = computed(() => {
  if (!planResult.value?.route) return []
  return planResult.value.route
})

// ===== 地图点击选点 =====
function startPick(type) {
  if (type === 'origin') { pickingOrigin.value = true; pickingDest.value = false }
  else { pickingDest.value = true; pickingOrigin.value = false }
}

function onMapClick(coord) {
  if (!coord || coord.lat == null || coord.lng == null) return
  if (pickingOrigin.value) {
    planForm.origin.lat = coord.lat
    planForm.origin.lng = coord.lng
    pickingOrigin.value = false
  } else if (pickingDest.value) {
    planForm.destination.lat = coord.lat
    planForm.destination.lng = coord.lng
    pickingDest.value = false
  }
}

function clearPoint(type) {
  if (type === 'origin') { planForm.origin.lat = null; planForm.origin.lng = null }
  else { planForm.destination.lat = null; planForm.destination.lng = null }
}

// ===== 调度记录 =====
const records = ref([])
const recordsLoading = ref(false)
const recordsTotal = ref(0)
const recordsPage = ref(1)
const recordsPageSize = ref(10)

// ===== 规划路径 =====
async function doPlan() {
  planLoading.value = true
  planResult.value = null
  try {
    const res = await emergencyApi.plan({
      vehicle_type: planForm.vehicle_type,
      origin: { lat: planForm.origin.lat, lng: planForm.origin.lng },
      destination: { lat: planForm.destination.lat, lng: planForm.destination.lng },
    })
    planResult.value = res.data?.data || res.data || {}
    ElMessage.success('路径规划完成')
  } catch (e) {
    const msg = e?.response?.data?.message || '规划失败，请检查坐标参数'
    ElMessage.error(msg)
  } finally {
    planLoading.value = false
  }
}

// ===== 创建调度记录 =====
async function doCreateRecord() {
  if (!planResult.value) { ElMessage.warning('请先规划路径'); return }
  createLoading.value = true
  try {
    await emergencyApi.createRecord({
      vehicle_type: planForm.vehicle_type,
      origin: { lat: planForm.origin.lat, lng: planForm.origin.lng },
      destination: { lat: planForm.destination.lat, lng: planForm.destination.lng },
      est_travel_time_sec: planResult.value.est_travel_time_sec,
      normal_travel_time_sec: planResult.value.normal_travel_time_sec,
      route: planResult.value.route || [],
      green_wave: planResult.value.green_wave || [],
    })
    ElMessage.success('调度记录已创建')
    planResult.value = null
    fetchRecords()
  } catch (e) {
    const msg = e?.response?.data?.message || '创建失败'
    ElMessage.error(msg)
  } finally {
    createLoading.value = false
  }
}

// ===== 获取调度记录 =====
async function fetchRecords() {
  recordsLoading.value = true
  try {
    const res = await emergencyApi.getRecords({ page: recordsPage.value, page_size: recordsPageSize.value })
    const data = res.data?.data || res.data || {}
    records.value = data.items || []
    recordsTotal.value = data.total || 0
  } catch {
    // silent
  } finally {
    recordsLoading.value = false
  }
}

// ===== 更新调度状态 =====
async function updateStatus(id, status) {
  const actionLabel = status === 'completed' ? '完成' : '取消'
  try {
    await ElMessageBox.confirm(`确认将此调度标记为"${actionLabel}"？`, '确认操作',
      { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' })
  } catch { return }
  try {
    await emergencyApi.updateStatus(id, status)
    ElMessage.success(`调度已${actionLabel}`)
    fetchRecords()
  } catch {
    ElMessage.error('状态更新失败')
  }
}

// ===== 工具函数 =====
function vehicleLabel(type) {
  const map = { ambulance: '🚑 救护车', fire: '🚒 消防车', police: '🚓 警车' }
  return map[type] || type || '—'
}

function statusLabel(status) {
  const map = { active: '进行中', completed: '已完成', cancelled: '已取消' }
  return map[status] || status || '—'
}

function statusType(status) {
  const map = { active: 'success', completed: 'primary', cancelled: 'info' }
  return map[status] || 'info'
}

function formatSec(sec) {
  if (sec == null) return '--'
  const m = Math.floor(sec / 60)
  const s = Math.round(sec % 60)
  if (m === 0) return `${s}秒`
  return `${m}分${s}秒`
}

function formatTimeStr(iso) {
  if (!iso) return ''
  try { return iso.replace('T', ' ').slice(0, 19) } catch { return iso }
}

// ===== 初始化 =====
onMounted(() => {
  fetchRecords()
})
</script>

<style scoped>
.emergency-view {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

/* 左列 420px 固定 */
.ev-left {
  width: 420px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 右列 flex:1 */
.ev-right {
  flex: 1;
  min-width: 0;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,.06);
}

@media (max-width: 1100px) {
  .emergency-view { flex-direction: column; }
  .ev-left { width: 100%; }
}

.ev-card {
  background: var(--bg-panel);
}
.card-title {
  font-weight: 600;
  color: var(--text-primary);
}

/* 坐标分段 */
.coord-section {
  background: rgba(255,255,255,.02);
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 4px;
  transition: border-color .2s, background .2s;
}
.coord-section.coord-picking {
  background: rgba(255,152,0,.08);
  border: 1px solid rgba(255,152,0,.3);
}
.coord-header {
  font-size: 12px;
  color: var(--text-secondary);
  padding-bottom: 4px;
  font-weight: 500;
  display: flex; align-items: center;
}
.coord-display {
  display: flex; align-items: center; justify-content: space-between;
  font-size: 13px; color: var(--accent-blue); font-family: monospace;
  padding: 4px 0;
}
.coord-val { font-weight: 500; }
.coord-empty {
  font-size: 12px; color: var(--text-secondary);
  padding: 6px 0; font-style: italic;
}

/* 规划结果 */
.result-highlight {
  border: 1px solid rgba(0,212,255,.15);
}
.result-stats {
  display: flex;
  gap: 8px;
  justify-content: center;
  flex-wrap: wrap;
}
.result-stat {
  text-align: center;
  min-width: 70px;
}
.rs-val {
  font-size: 22px;
  font-weight: 700;
  line-height: 1.2;
}
.rs-lbl {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 2px;
}
.result-detail {
  background: rgba(255,255,255,.02);
  border-radius: 6px;
  padding: 8px 12px;
  margin-top: 8px;
}
.detail-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  padding: 2px 0;
}
.detail-label {
  color: var(--text-secondary);
}
.detail-value {
  color: var(--text-primary);
  font-weight: 500;
}

/* 分页 */
.ev-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}
</style>
