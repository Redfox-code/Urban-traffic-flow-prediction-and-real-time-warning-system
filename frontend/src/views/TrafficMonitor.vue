<template>
  <div style="display:flex;gap:20px;height:calc(100vh - 120px)">
    <div style="flex:1;min-width:0">
      <el-card shadow="never" style="height:100%">
        <TrafficMap :sections="sections" :traffic-data="trafficData" :map-height="'100%'" @section-click="onSectionClick" />
      </el-card>
    </div>
    <div style="width:360px;display:flex;flex-direction:column;gap:16px">
      <el-card shadow="never">
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
          <el-button size="small" type="success" @click="startSim" :disabled="simStore.realtimeRunning">▶ 开始仿真</el-button>
          <el-button size="small" type="danger" @click="stopSim" :disabled="!simStore.realtimeRunning">⏹ 停止仿真</el-button>
          <span v-if="simStore.realtimeRunning" style="font-size:12px;color:#00e676">🟢 运行中</span>
          <span class="update-timer">刷新 {{ timer }}s 前</span>
        </div>
        <el-progress v-if="simStore.realtimeRunning" :percentage="simStore.progress" :stroke-width="4" style="margin-top:8px" :color="'#00d4ff'" />
      </el-card>
      <el-card shadow="never">
        <template #header><span style="font-weight:bold;color:var(--text-primary)">📍 路段列表</span></template>
        <el-scrollbar max-height="240px">
          <div v-for="s in sections" :key="s.id" class="section-item"
               :class="{active: s.id === selectedId, flash: flashes[s.id]}" @click="onSectionClick(s)">
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>{{ s.name }}</span>
              <TrafficBadge :occupancy="trafficData[s.id]?.occupancy || 0" />
            </div>
            <div class="section-sub">{{ trafficData[s.id]?.vehicle_count || 0 }} veh · {{ trafficData[s.id]?.avg_speed || 0 }} km/h</div>
          </div>
        </el-scrollbar>
      </el-card>
      <el-card shadow="never" v-if="selectedSection">
        <template #header><span style="font-weight:bold;color:var(--accent-blue)">📊 {{ selectedSection.name }}</span></template>
        <div v-if="trafficData[selectedId]" class="realtime-data">
          <div class="data-row"><span>车流量</span><b class="val">{{ trafficData[selectedId].vehicle_count || '--' }} <small>veh</small></b></div>
          <div class="data-row"><span>平均速度</span><b class="val">{{ trafficData[selectedId].avg_speed || '--' }} <small>km/h</small></b></div>
          <div class="data-row"><span>占有率</span><b class="val">{{ trafficData[selectedId].occupancy || '--' }}<small>%</small></b></div>
          <div class="data-row"><span>通行能力</span><b>{{ selectedSection.capacity }} veh/h</b></div>
          <div class="data-row"><span>限速</span><b>{{ selectedSection.max_speed }} km/h</b></div>
        </div>
        <div v-else style="color:var(--text-secondary);text-align:center;padding:20px">暂无实时数据</div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { sectionsApi } from '@/api/sections'
import { trafficApi } from '@/api/traffic'
import { useSimulationStore } from '@/store/simulation'
import TrafficMap from '@/components/map/TrafficMap.vue'
import TrafficBadge from '@/components/common/TrafficBadge.vue'

const simStore = useSimulationStore()
const startSim = () => simStore.startRealtime()
const stopSim = () => simStore.stopRealtime()

const sections = ref([]); const selectedId = ref(null); const selectedSection = ref(null)
const trafficData = reactive({}); const flashes = reactive({})
const timer = ref(0); const lastUpdate = ref(0); let timerInterval = null

const loadAllTraffic = async () => {
  try {
    const res = await trafficApi.getCurrent(); const data = res.data || res
    if (Array.isArray(data)) {
      data.forEach(d => {
        const old = trafficData[d.section_id]
        if (old && (old.vehicle_count !== d.vehicle_count || Math.abs(old.occupancy - d.occupancy) > 1)) {
          flashes[d.section_id] = true; setTimeout(() => { flashes[d.section_id] = false }, 500)
        }
        trafficData[d.section_id] = d
      })
    }
    lastUpdate.value = Date.now(); timer.value = 0
  } catch {}
}

const onSectionClick = async (section) => {
  selectedId.value = section.id; selectedSection.value = section
  if (!trafficData[section.id]) {
    try { const res = await trafficApi.getCurrent(section.id); const data = res.data || res; if (Array.isArray(data) && data.length > 0) trafficData[data[0].section_id] = data[0] } catch {}
  }
}

let refreshTimer = null
onMounted(async () => {
  simStore.checkStatus()
  try { const res = await sectionsApi.getList(); sections.value = res.data?.items || res?.items || [] } catch {}
  loadAllTraffic()
  refreshTimer = setInterval(loadAllTraffic, 5000)
  timerInterval = setInterval(() => { if (lastUpdate.value) timer.value = Math.floor((Date.now() - lastUpdate.value) / 1000) }, 1000)
  setInterval(() => simStore.checkStatus(), 2000)
})
onUnmounted(() => { clearInterval(refreshTimer); clearInterval(timerInterval) })
</script>

<style scoped>
.section-item { padding:12px; border-radius:8px; cursor:pointer; transition:background .3s, transform .2s; border-bottom:1px solid rgba(255,255,255,.04); }
.section-item:hover, .section-item.active { background:rgba(0,212,255,.08); }
.section-item.flash { background:rgba(0,212,255,.15); transform:scale(1.02); }
.section-sub { font-size:12px; color:var(--text-secondary); margin-top:4px; }
.realtime-data { display:flex; flex-direction:column; gap:12px; }
.data-row { display:flex; justify-content:space-between; color:var(--text-secondary); font-size:14px; }
.data-row b { color:var(--text-primary); }
.data-row b.val { transition: all .3s; }
.data-row small { font-size:11px; color:var(--text-secondary); }
.update-timer { font-size:11px; color:var(--text-secondary); margin-left:4px; min-width:80px; }
</style>
