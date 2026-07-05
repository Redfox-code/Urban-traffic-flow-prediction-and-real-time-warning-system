<template>
  <div>
    <h2 style="color:var(--text-primary);margin-bottom:24px">系统首页</h2>
    <el-row :gutter="20">
      <el-col :span="6" v-for="card in statsCards" :key="card.title">
        <div class="stat-card">
          <div class="stat-icon" :style="{background:card.color}">{{ card.icon }}</div>
          <div class="stat-info"><div class="stat-value">{{ card.value }}</div><div class="stat-title">{{ card.title }}</div></div>
        </div>
      </el-col>
    </el-row>

    <!-- 仿真面板：实时在上，离线在下 -->
    <el-card shadow="never" style="background:var(--bg-panel);margin-top:20px">
      <template #header><div style="font-weight:bold;color:var(--text-primary)">🔴 实时仿真</div></template>
      <p style="color:var(--text-secondary);font-size:13px;margin-bottom:12px">启动后 SUMO 将实时运行，数据持续写入数据库，路况监控页面每5秒自动刷新。</p>
      <div style="display:flex;gap:10px;align-items:center">
        <el-button type="success" @click="simStore.startRealtime()" :disabled="simStore.realtimeRunning">
          {{ simStore.realtimeRunning ? '🟢 运行中' : '▶ 启动实时仿真' }}
        </el-button>
        <el-button type="danger" @click="simStore.stopRealtime()" :disabled="!simStore.realtimeRunning">⏹ 停止</el-button>
        <span v-if="simStore.message && (simStore.message.includes('启动')||simStore.message.includes('停止'))"
              :style="{color: simStore.message.includes('✅')||simStore.message.includes('启动') ? '#00e676' : '#f44336', fontSize:'13px'}">{{ simStore.message }}</span>
      </div>
    </el-card>

    <el-card shadow="never" style="background:var(--bg-panel);margin-top:16px">
      <template #header><div style="font-weight:bold;color:var(--text-primary)">📁 离线仿真</div></template>
      <p style="color:var(--text-secondary);font-size:13px;margin-bottom:12px">上传 SUMO 输出文件（e2_output.xml），系统将解析并导入数据库进行静态分析。</p>
      <el-upload drag :action="uploadUrl" :headers="authHeader" :on-success="onUploadOk" :on-error="onUploadErr" accept=".xml" style="margin-bottom:12px">
        <div style="padding:20px 0">
          <div style="font-size:28px;margin-bottom:8px">📂</div>
          <div style="color:var(--text-primary);font-size:14px">拖拽文件到此处或<em style="color:var(--accent-blue)">点击上传</em></div>
          <div style="color:var(--text-secondary);font-size:12px;margin-top:4px">支持 .xml 格式的 SUMO 输出文件</div>
        </div>
      </el-upload>
      <div style="display:flex;gap:10px;align-items:center;margin-bottom:12px">
        <el-button type="primary" @click="simStore.runBatch()" :loading="simStore.batchRunning" :disabled="simStore.batchRunning">
          {{ simStore.batchRunning ? '运行中...' : '▶ 一键自动仿真' }}
        </el-button>
        <el-button type="danger" size="small" @click="simStore.stopBatch()" :disabled="!simStore.batchRunning">⏹ 停止</el-button>
        <el-button size="small" @click="loadHistory">📋 提交记录</el-button>
        <span v-if="simStore.message && simStore.message.includes('完成')" :style="{color: simStore.message.includes('✅')?'#00e676':'#f44336',fontSize:'13px'}">{{ simStore.message }}</span>
      </div>
      <el-table v-if="history.length" :data="history" size="small" style="background:transparent" max-height="200px">
        <el-table-column prop="id" label="#" width="50" />
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column prop="status" label="状态" width="80"><template #default="{row}"><el-tag :type="row.status==='completed'?'success':'info'" size="small">{{ row.status }}</el-tag></template></el-table-column>
        <el-table-column prop="records" label="条数" width="60" />
        <el-table-column label="" width="60"><template #default="{row}"><el-button size="small" @click="loadSim(row.id)">读取</el-button></template></el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { statsApi } from '@/api/stats'
import { useUserStore } from '@/store/user'
import { useSimulationStore } from '@/store/simulation'
import request from '@/api/request'

const userStore = useUserStore()
const simStore = useSimulationStore()
const starting = ref(false)
const history = ref([])

const uploadUrl = (import.meta.env.VITE_API_BASE_URL || '') + '/simulation/upload'
const authHeader = computed(() => ({ Authorization: `Bearer ${userStore.token}` }))

const onUploadOk = () => { ElMessage.success('上传成功'); loadHistory() }
const onUploadErr = () => ElMessage.error('上传失败')
const loadHistory = async () => {
  try { const res = await request.get('/simulation/list', { params: { type: 'batch' } }); history.value = res.data?.items || res?.items || [] } catch {}
}
const loadSim = async (id) => {
  try { const res = await request.post(`/simulation/${id}/load`); ElMessage.success(`导入${res.data?.records_imported || 0}条`) } catch (e) { ElMessage.error(e?.message || '失败') }
}

const statsCards = ref([
  { icon:'🛣️', title:'路段总数', value:0, color:'linear-gradient(135deg,#00d4ff,#0099cc)' },
  { icon:'📡', title:'检测器数', value:0, color:'linear-gradient(135deg,#00e676,#00b248)' },
  { icon:'⚠️', title:'今日预警', value:0, color:'linear-gradient(135deg,#ff9800,#f57c00)' },
  { icon:'📈', title:'预测精度(RF)', value:'--', color:'linear-gradient(135deg,#ab47bc,#7b1fa2)' },
])
onMounted(async () => {
  simStore.checkStatus()
  try { const d = (await statsApi.getDashboard()).data || {}; statsCards.value[0].value = d.total_sections || 0; statsCards.value[1].value = d.active_detectors || 0; statsCards.value[2].value = d.today_warnings || 0; statsCards.value[3].value = (d.avg_prediction_accuracy || 0) + '%' } catch {}
})
</script>

<style scoped>
.stat-card { background: var(--bg-panel); border-radius: 12px; padding: 24px; display: flex; align-items: center; gap: 16px; transition: transform .2s, box-shadow .2s; cursor: default; }
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 20px rgba(0,212,255,.15); }
.stat-icon { width: 52px; height: 52px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; flex-shrink: 0; }
.stat-value { font-size: 28px; font-weight: bold; color: var(--text-primary); }
.stat-title { font-size: 13px; color: var(--text-secondary); margin-top: 2px; }
</style>
