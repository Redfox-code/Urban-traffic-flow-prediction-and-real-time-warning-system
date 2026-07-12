<template>
  <div style="color:var(--text-primary);height:calc(100vh - 120px)">
    <h2>路径规划 <span style="font-size:13px;color:var(--text-secondary);font-weight:normal">点击地图路段快速选择起终点</span></h2>
    <div style="display:flex;gap:20px;height:calc(100% - 50px)">
      <!-- 左侧：表单 + 结果 -->
      <div style="width:420px;display:flex;flex-direction:column;gap:16px;overflow-y:auto">
        <!-- 表单 -->
        <el-card shadow="never" style="background:var(--bg-panel)">
          <div style="display:flex;flex-direction:column;gap:12px">
            <!-- 起点 -->
            <div>
              <div style="font-size:13px;color:var(--text-secondary);margin-bottom:4px">
                🟢 起点路段
                <span v-if="pickingOrigin" style="color:var(--accent-blue);font-size:12px">— 点击地图选择</span>
              </div>
              <el-select v-model="origin" placeholder="选择起点或点击地图" filterable style="width:100%"
                @focus="pickingOrigin = true" @change="pickingOrigin = false">
                <el-option v-for="s in sections" :key="s.id" :label="s.name" :value="s.id" />
              </el-select>
            </div>

            <!-- 交换按钮 -->
            <div style="display:flex;justify-content:center">
              <el-button circle size="small" @click="swapPoints" :disabled="!origin && !dest" title="交换起终点">
                ⇅
              </el-button>
            </div>

            <!-- 终点 -->
            <div>
              <div style="font-size:13px;color:var(--text-secondary);margin-bottom:4px">
                🔴 终点路段
                <span v-if="pickingDest" style="color:#ff4d4f;font-size:12px">— 点击地图选择</span>
              </div>
              <el-select v-model="dest" placeholder="选择终点或点击地图" filterable style="width:100%"
                @focus="pickingDest = true" @change="pickingDest = false">
                <el-option v-for="s in sections" :key="s.id" :label="s.name" :value="s.id" />
              </el-select>
            </div>

            <el-button type="primary" @click="planRoute" :loading="loading" :disabled="!origin || !dest" style="width:100%">
              <span v-if="!loading">🚘 规划路径</span>
              <span v-else>规划中...</span>
            </el-button>

            <!-- 错误提示 -->
            <el-alert v-if="errorMsg" :title="errorMsg" type="error" show-icon :closable="true" @close="errorMsg = ''" />
          </div>
        </el-card>

        <!-- 结果 -->
        <el-card v-if="result" shadow="never" style="background:var(--bg-panel)">
          <template #header>
            <span style="font-weight:bold;color:var(--accent-blue)">📍 规划结果</span>
          </template>
          <div style="display:flex;gap:16px;margin-bottom:16px">
            <div style="flex:1;text-align:center;padding:12px;background:rgba(0,212,255,.08);border-radius:8px">
              <div style="font-size:12px;color:var(--text-secondary)">总距离</div>
              <div style="font-size:24px;font-weight:bold;color:var(--accent-blue)">{{ result.total_distance }} <small>km</small></div>
            </div>
            <div style="flex:1;text-align:center;padding:12px;background:rgba(0,212,255,.08);border-radius:8px">
              <div style="font-size:12px;color:var(--text-secondary)">预计时间</div>
              <div style="font-size:24px;font-weight:bold;color:var(--accent-blue)">{{ result.estimated_time }} <small>min</small></div>
            </div>
          </div>

          <!-- 途经路段 -->
          <div style="font-size:13px;color:var(--text-secondary);margin-bottom:8px">
            途经 {{ result.path.length }} 个路段
          </div>
          <div v-for="(p, i) in result.path" :key="i" class="route-segment">
            <div class="segment-num">{{ i + 1 }}</div>
            <div class="segment-info">
              <div class="segment-name">{{ p.name }}</div>
              <div class="segment-sub">
                {{ p.length || 0 }} km
                <span v-if="p.avg_speed != null && p.avg_speed > 0" style="margin-left:8px">🚗 {{ p.avg_speed }} km/h</span>
                <span v-if="p.occupancy != null" style="margin-left:4px">
                  <el-tag size="small"
                    :type="p.occupancy < 30 ? 'success' : p.occupancy < 60 ? 'warning' : 'danger'"
                    effect="dark">
                    {{ p.occupancy < 30 ? '畅通' : p.occupancy < 60 ? '缓行' : p.occupancy < 85 ? '拥堵' : '严重' }}
                  </el-tag>
                </span>
                <span v-else style="margin-left:4px">
                  <el-tag size="small" type="info" effect="plain">无实时数据</el-tag>
                </span>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 预测联动提示 -->
        <el-card v-if="result" shadow="never" style="background:var(--bg-panel)">
          <div style="font-size:13px;color:var(--text-secondary)">
            📊 想了解这条路径的未来交通状况？
            <el-link type="primary" @click="$router.push('/prediction')" style="font-size:13px">前往流量预测 →</el-link>
          </div>
        </el-card>
      </div>

      <!-- 右侧：地图 -->
      <div style="flex:1;min-width:0">
        <el-card shadow="never" style="height:100%;background:var(--bg-panel)">
          <TrafficMap :route-path="routeCoords" :map-height="'100%'" @section-click="onMapClick" />
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { routeApi } from '@/api/routePlan'
import { sectionsApi } from '@/api/sections'
import TrafficMap from '@/components/map/TrafficMap.vue'

const sections = ref([])
const origin = ref(null)
const dest = ref(null)
const loading = ref(false)
const result = ref(null)
const routeCoords = ref([])
const errorMsg = ref('')
const pickingOrigin = ref(false)
const pickingDest = ref(false)

onMounted(async () => {
  try {
    const res = await sectionsApi.getList()
    sections.value = res.data?.items || res?.items || []
  } catch (e) {
    console.warn('加载路段列表失败', e)
  }
})

/** 交换起终点 */
const swapPoints = () => {
  const tmp = origin.value
  origin.value = dest.value
  dest.value = tmp
}

/** 地图点击路段 → 智能填入起点或终点 */
const onMapClick = (data) => {
  if (!data || !data.name) return
  // 找到匹配的路段
  const matched = sections.value.find(s => s.name === data.name || data.name.includes(s.name) || s.name.includes(data.name))
  if (!matched) return

  if (pickingOrigin.value) {
    // 正在设置起点
    origin.value = matched.id
    pickingOrigin.value = false
  } else if (pickingDest.value) {
    // 正在设置终点
    dest.value = matched.id
    pickingDest.value = false
  } else if (!origin.value) {
    // 起点未设置 → 填起点
    origin.value = matched.id
  } else if (!dest.value) {
    // 终点未设置 → 填终点
    dest.value = matched.id
  } else {
    // 都已设置 → 覆盖终点（常见：修改终点）
    dest.value = matched.id
  }
}

/** 规划路径 */
const planRoute = async () => {
  if (!origin.value || !dest.value) {
    errorMsg.value = '请选择起点和终点路段'
    return
  }
  errorMsg.value = ''
  loading.value = true
  result.value = null
  routeCoords.value = []
  try {
    const res = await routeApi.plan({
      origin_section_id: origin.value,
      dest_section_id: dest.value,
    })
    const data = res.data || res
    if (!data || !data.path) {
      errorMsg.value = '规划失败，请尝试其他路段组合'
      return
    }
    result.value = data
    // 使用 route_segments（每段独立坐标），地图分段绘制避免走到路外
    routeCoords.value = data.route_segments || []
  } catch (e) {
    const msg = e?.response?.data?.message || e?.message || '网络请求失败'
    errorMsg.value = msg
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.route-segment { display:flex; gap:12px; padding:10px 0; border-bottom:1px solid rgba(255,255,255,.04); align-items:flex-start }
.segment-num { width:24px; height:24px; background:rgba(0,212,255,.15); color:var(--accent-blue); border-radius:50%; text-align:center; line-height:24px; font-size:12px; font-weight:bold; flex-shrink:0 }
.segment-info { flex:1 }
.segment-name { font-size:14px; font-weight:500 }
.segment-sub { font-size:12px; color:var(--text-secondary); margin-top:2px }
</style>
