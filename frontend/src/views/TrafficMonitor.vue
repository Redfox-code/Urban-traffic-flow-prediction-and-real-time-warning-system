<template>
  <div style="display:flex;gap:20px;height:calc(100vh - 120px)">
    <div style="flex:1;min-width:0">
      <el-card shadow="never" style="height:100%">
        <TrafficMap :sections="sections" :map-height="'100%'" @section-click="onSectionClick" />
      </el-card>
    </div>
    <div style="width:360px;display:flex;flex-direction:column;gap:16px">
      <el-card shadow="never">
        <div style="display:flex;gap:8px;align-items:center">
          <el-button size="small" type="success" @click="startSim" :disabled="rtRunning">▶ 开始仿真</el-button>
          <el-button size="small" type="danger" @click="stopSim" :disabled="!rtRunning">⏹ 停止仿真</el-button>
          <span v-if="rtRunning" style="font-size:12px;color:#00e676">🟢 运行中</span>
        </div>
      </el-card>
      <el-card shadow="never">
        <template #header><span style="font-weight:bold;color:var(--text-primary)">📍 路段列表</span></template>
        <el-scrollbar max-height="250px">
          <div v-for="s in sections" :key="s.id" class="section-item" :class="{active: s.id === selectedId}" @click="onSectionClick(s)">
            <div style="display:flex;justify-content:space-between;align-items:center"><span>{{ s.name }}</span><TrafficBadge :occupancy="trafficData[s.id]?.occupancy || 0" /></div>
            <div class="section-sub">{{ s.capacity }} veh/h · {{ s.max_speed }} km/h</div>
          </div>
        </el-scrollbar>
      </el-card>
      <el-card shadow="never" v-if="selectedSection">
        <template #header><span style="font-weight:bold;color:var(--accent-blue)">📊 {{ selectedSection.name }}</span></template>
        <div v-if="trafficData[selectedId]" class="realtime-data">
          <div class="data-row"><span>车流量</span><b>{{ trafficData[selectedId].vehicle_count || '--' }} veh</b></div>
          <div class="data-row"><span>平均速度</span><b>{{ trafficData[selectedId].avg_speed || '--' }} km/h</b></div>
          <div class="data-row"><span>占有率</span><b>{{ trafficData[selectedId].occupancy || '--' }}%</b></div>
          <div class="data-row"><span>通行能力</span><b>{{ selectedSection.capacity }} veh/h</b></div>
          <div class="data-row"><span>限速</span><b>{{ selectedSection.max_speed }} km/h</b></div>
        </div>
        <div v-else-if="loadingAll" style="color:var(--text-secondary);text-align:center;padding:20px">加载中...</div>
        <div v-else style="color:var(--text-secondary);text-align:center;padding:20px">暂无实时数据</div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { sectionsApi } from '@/api/sections'
import { trafficApi } from '@/api/traffic'
import request from '@/api/request'
import TrafficMap from '@/components/map/TrafficMap.vue'
import TrafficBadge from '@/components/common/TrafficBadge.vue'

const rtRunning = ref(false)
const startSim = async () => {
  try { await request.post('/sumo/run_realtime', null, { timeout: 10000 }); rtRunning.value = true; ElMessage.success('实时仿真已启动') }
  catch (e) { ElMessage.error('启动失败') }
}
const stopSim = async () => {
  try { await request.post('/sumo/stop'); rtRunning.value = false; ElMessage.success('已停止') }
  catch { rtRunning.value = false }
}

const sections = ref([]); const selectedId = ref(null); const selectedSection = ref(null)
const trafficData = reactive({}); const loadingAll = ref(false)

const loadAllTraffic = async () => {
  loadingAll.value = true
  try { const res = await trafficApi.getCurrent(); const data = res.data || res; if (Array.isArray(data)) data.forEach(d => { trafficData[d.section_id] = d }) } catch {}
  loadingAll.value = false
}
const onSectionClick = async (section) => {
  selectedId.value = section.id; selectedSection.value = section
  if (!trafficData[section.id]) {
    try { const res = await trafficApi.getCurrent(section.id); const data = res.data || res; if (Array.isArray(data) && data.length > 0) trafficData[data[0].section_id] = data[0] } catch {}
  }
}

let refreshTimer = null
onMounted(async () => {
  try { const s = await request.get('/sumo/status'); rtRunning.value = s.data?.running || s?.running || false } catch {}
  try { const res = await sectionsApi.getList(); sections.value = res.data?.items || res?.items || [] } catch {}
  loadAllTraffic()
  refreshTimer = setInterval(loadAllTraffic, 5000)
})
onUnmounted(() => { clearInterval(refreshTimer) })
</script>

<style scoped>
.section-item { padding:12px; border-radius:8px; cursor:pointer; transition:background .2s; border-bottom:1px solid rgba(255,255,255,.04); }
.section-item:hover, .section-item.active { background:rgba(0,212,255,.08); }
.section-sub { font-size:12px; color:var(--text-secondary); margin-top:4px; }
.realtime-data { display:flex; flex-direction:column; gap:12px; }
.data-row { display:flex; justify-content:space-between; color:var(--text-secondary); font-size:14px; }
.data-row b { color:var(--text-primary); }
</style>
