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

    <el-card style="background:var(--bg-panel);margin-top:20px">
      <template #header><span style="font-weight:bold;color:var(--text-primary)">🔬 仿真控制</span></template>
      <el-tabs v-model="simTab">
        <el-tab-pane label="实时仿真" name="realtime">
          <div style="display:flex;align-items:center;gap:12px">
            <el-button type="success" @click="runRealtime" :loading="rtStarting" :disabled="rtRunning">
              {{ rtRunning ? '🟢 运行中...' : '▶ 启动实时仿真' }}
            </el-button>
            <el-button type="danger" @click="stopRealtime" :disabled="!rtRunning">⏹ 停止仿真</el-button>
            <span v-if="sumoResult" :style="{color: sumoResult.includes('✅')||sumoResult.includes('启动') ? '#00e676' : '#f44336'}">{{ sumoResult }}</span>
          </div>
        </el-tab-pane>

        <el-tab-pane label="离线仿真" name="batch">
          <div style="margin-bottom:12px;color:var(--text-secondary);font-size:13px">
            提交 SUMO 输出文件（e2_output.xml）进行批量导入分析。可查看历史提交记录。
          </div>
          <el-upload :action="uploadUrl" :headers="authHeader" :on-success="onUploadOk" :on-error="onUploadErr"
                     accept=".xml" :limit="1" style="display:inline-block;margin-right:12px">
            <el-button type="primary">📁 选择文件上传</el-button>
          </el-upload>
          <el-button @click="loadHistory" style="margin-left:8px">📋 提交历史</el-button>

          <el-table v-if="history.length" :data="history" style="margin-top:16px;background:var(--bg-panel)" size="small">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="type" label="类型" width="80" />
            <el-table-column prop="status" label="状态" width="90"><template #default="{row}"><el-tag :type="row.status==='completed'?'success':row.status==='failed'?'danger':'info'">{{ row.status }}</el-tag></template></el-table-column>
            <el-table-column prop="records" label="记录数" width="80" />
            <el-table-column label="操作" width="120"><template #default="{row}">
              <el-button size="small" type="primary" @click="loadSim(row.id)" :disabled="row.status==='running'">读取</el-button>
            </template></el-table-column>
          </el-table>

          <el-button type="primary" @click="runSumo" :loading="sumoRunning" :disabled="sumoRunning" style="margin-top:12px">
            {{ sumoRunning ? '仿真运行中...' : '▶ 一键运行仿真(自动)' }}
          </el-button>
          <span style="margin-left:8px;font-size:12px;color:var(--text-secondary)">自动生成路网→运行SUMO→导入数据</span>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { statsApi } from '@/api/stats'
import { useUserStore } from '@/store/user'
import request from '@/api/request'

const userStore = useUserStore()
const simTab = ref('realtime')
const sumoRunning = ref(false); const sumoResult = ref('')
const rtRunning = ref(false); const rtStarting = ref(false)
const history = ref([])

const uploadUrl = import.meta.env.VITE_API_BASE_URL + '/simulation/upload'
const authHeader = computed(() => ({ Authorization: `Bearer ${userStore.token}` }))

const runRealtime = async () => {
  rtStarting.value = true; sumoResult.value = ''
  try { const res = await request.post('/sumo/run_realtime', null, { timeout: 10000 }); sumoResult.value = '✅ 实时仿真已启动'; rtRunning.value = true; ElMessage.success('已启动') }
  catch (e) { sumoResult.value = '❌ ' + (e?.message || '失败') }
  finally { rtStarting.value = false }
}
const stopRealtime = async () => {
  try { await request.post('/sumo/stop'); rtRunning.value = false; sumoResult.value = '⏹ 已停止'; ElMessage.success('已停止') }
  catch { rtRunning.value = false }
}

const runSumo = async () => {
  sumoRunning.value = true; sumoResult.value = ''
  try { const res = await request.post('/sumo/run', null, { timeout: 180000 }); const d = res.data || res; sumoResult.value = `✅ 完成 (${d.records_imported || 0}条)` }
  catch (e) { sumoResult.value = '❌ ' + (e?.message || '失败') }
  finally { sumoRunning.value = false }
}

const loadHistory = async () => {
  try { const res = await request.get('/simulation/list', { params: { type: simTab.value } }); history.value = res.data?.items || res?.items || [] }
  catch {}
}
const loadSim = async (id) => {
  try { const res = await request.post(`/simulation/${id}/load`); ElMessage.success(`导入${res.data?.records_imported || 0}条`) }
  catch (e) { ElMessage.error(e?.message || '失败') }
}
const onUploadOk = () => { ElMessage.success('上传成功'); loadHistory() }
const onUploadErr = () => ElMessage.error('上传失败')

const statsCards = ref([
  { icon:'🛣️', title:'路段总数', value:0, color:'linear-gradient(135deg,#00d4ff,#0099cc)' },
  { icon:'📡', title:'检测器数', value:0, color:'linear-gradient(135deg,#00e676,#00b248)' },
  { icon:'⚠️', title:'今日预警', value:0, color:'linear-gradient(135deg,#ff9800,#f57c00)' },
  { icon:'📈', title:'预测精度(RF)', value:'--', color:'linear-gradient(135deg,#ab47bc,#7b1fa2)' },
])
onMounted(async () => {
  try { const res = await statsApi.getDashboard(); const d = res.data || res; statsCards.value[0].value = d.total_sections || 0; statsCards.value[1].value = d.active_detectors || 0; statsCards.value[2].value = d.today_warnings || 0; statsCards.value[3].value = (d.avg_prediction_accuracy || 0) + '%' } catch {}
  // 检查实时仿真状态
  try { const s = await request.get('/sumo/status'); rtRunning.value = s.data?.running || s?.running || false } catch {}
})
</script>

<style scoped>
.stat-card { background: var(--bg-panel); border-radius: 12px; padding: 24px; display: flex; align-items: center; gap: 16px; transition: transform .2s, box-shadow .2s; cursor: default; }
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 20px rgba(0,212,255,.15); }
.stat-icon { width: 52px; height: 52px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; flex-shrink: 0; }
.stat-value { font-size: 28px; font-weight: bold; color: var(--text-primary); }
.stat-title { font-size: 13px; color: var(--text-secondary); margin-top: 2px; }
</style>
