<template>
  <div class="signal-view">
    <div class="signal-header-stats">
      <div class="signal-stat-card">
        <span class="ss-num" style="color:#4caf50">{{ signalStats.total_optimizations || 0 }}</span>
        <span class="ss-label">总优化次数</span>
      </div>
      <div class="signal-stat-card">
        <span class="ss-num" style="color:#2196f3">{{ signalStats.applied_count || 0 }}</span>
        <span class="ss-label">已应用方案</span>
      </div>
      <div class="signal-stat-card">
        <span class="ss-num" style="color:#ff9800">{{ signalStats.average_efficiency_gain_pct || 0 }}%</span>
        <span class="ss-label">平均效率提升</span>
      </div>
    </div>

    <div class="signal-grid">
      <el-card shadow="never" class="signal-card">
        <template #header><span class="card-title">🔧 Webster 配时计算</span></template>
        <el-form label-width="110px" size="default">
          <el-form-item label="路口名称">
            <el-select v-model="calcForm.intersection_name" placeholder="选择路口或手动输入" filterable allow-create style="width:100%">
              <el-option v-for="it in intersections" :key="it.intersection_id" :label="it.intersection_name" :value="it.intersection_name" />
            </el-select>
          </el-form-item>
          <el-form-item label="当前周期(s)"><el-input-number v-model="calcForm.current_cycle" :min="30" :max="240" :step="5" /></el-form-item>
          <el-form-item label="相位数"><el-input-number v-model="calcForm.phase_count" :min="2" :max="6" :step="1" /></el-form-item>
          <el-form-item label="损失时间(s)"><el-input-number v-model="calcForm.lost_time" :min="1" :max="20" :step="0.5" :precision="1" /></el-form-item>
          <el-form-item label="总流量(veh/h)"><el-input-number v-model="calcForm.total_flow" :min="100" :max="5000" :step="100" /></el-form-item>
          <el-form-item label="饱和流量(veh/h)"><el-input-number v-model="calcForm.saturation_flow" :min="500" :max="3000" :step="100" /></el-form-item>
          <el-form-item>
            <el-button type="primary" @click="doCalculate" :loading="calcLoading" style="width:100%">🧮 计算最优配时</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <div class="signal-right">
        <el-card v-if="calcResult" shadow="never" class="signal-card result-card">
          <template #header><span class="card-title">📊 计算结果</span></template>
          <div class="result-grid">
            <div class="result-item">
              <div class="result-val" style="color:#00d4ff">{{ calcResult.optimal_cycle }}s</div>
              <div class="result-lbl">最优周期</div>
            </div>
            <div class="result-item">
              <div class="result-val" :style="{ color: (calcResult.efficiency_gain_pct || 0) > 0 ? '#4caf50' : '#ff9800' }">{{ calcResult.efficiency_gain_pct || 0 }}%</div>
              <div class="result-lbl">效率提升</div>
            </div>
            <div class="result-item">
              <div class="result-val" style="color:#2196f3">{{ calcResult.delay_reduction_sec || 0 }}s</div>
              <div class="result-lbl">延误减少</div>
            </div>
          </div>
          <div v-if="calcResult.green_splits" class="green-splits">
            <div class="split-title">🟢 绿信比分配</div>
            <div v-for="(ratio, phase) in Object.entries(calcResult.green_splits)" :key="phase" class="split-row">
              <span>{{ phase }}</span>
              <div class="split-bar"><div class="split-fill" :style="{ width: (ratio * 100) + '%' }"></div></div>
              <span>{{ Math.round(ratio * 100) }}%</span>
            </div>
          </div>
          <el-button v-if="calcResult.optimization_id" type="success" size="default" style="margin-top:12px;width:100%"
            @click="doApply(calcResult.optimization_id)" :loading="applyLoading">✅ 应用此配时方案</el-button>
        </el-card>

        <el-card shadow="never" class="signal-card">
          <template #header>
            <span class="card-title">📜 优化历史</span>
            <el-button text size="small" @click="fetchHistory" :loading="histLoading">🔄</el-button>
          </template>
          <el-table :data="history" size="small" style="width:100%" max-height="360" v-loading="histLoading">
            <el-table-column prop="intersection_name" label="路口" min-width="100" show-overflow-tooltip />
            <el-table-column prop="current_cycle" label="当前(s)" width="75" />
            <el-table-column prop="suggested_cycle" label="建议(s)" width="75" />
            <el-table-column prop="efficiency_gain_pct" label="效率提升" width="85">
              <template #default="{row}">{{ row.efficiency_gain_pct }}%</template>
            </el-table-column>
            <el-table-column prop="delay_reduction_sec" label="减延误(s)" width="85" />
            <el-table-column prop="is_applied" label="状态" width="80">
              <template #default="{row}">
                <el-tag size="small" :type="row.is_applied ? 'success' : 'info'" effect="plain">{{ row.is_applied ? '已应用' : '未应用' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" width="150">
              <template #default="{row}">{{ formatTime(row.created_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="70">
              <template #default="{row}">
                <el-button v-if="!row.is_applied" type="primary" link size="small" @click="doApply(row.id)">应用</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { signalApi } from '@/api/signal'
import { ElMessage } from 'element-plus'

const intersections = ref([])
const history = ref([])
const calcResult = ref(null)
const calcLoading = ref(false)
const applyLoading = ref(false)
const histLoading = ref(false)

const signalStats = reactive({ total_optimizations: 0, applied_count: 0, average_efficiency_gain_pct: 0 })

const calcForm = reactive({
  intersection_name: '', current_cycle: 120, phase_count: 4, lost_time: 2, total_flow: 2000, saturation_flow: 1800,
})

async function fetchIntersections() {
  try { const res = await signalApi.getIntersections(); intersections.value = (res.data?.data?.intersections || res.data?.intersections || []) } catch { /* empty */ }
}
async function fetchStats() {
  try { const res = await signalApi.getStats(); Object.assign(signalStats, res.data?.data || res.data || {}) } catch { /* defaults */ }
}
async function fetchHistory() {
  histLoading.value = true
  try { const res = await signalApi.getHistory(); history.value = (res.data?.data?.items || res.data?.items || []) }
  finally { histLoading.value = false }
}

async function doCalculate() {
  if (!calcForm.intersection_name) { ElMessage.warning('请输入路口名称'); return }
  calcLoading.value = true; calcResult.value = null
  try {
    const res = await signalApi.calculate({
      intersection_id: calcForm.intersection_name.replace(/\s+/g, '_').toLowerCase(),
      intersection_name: calcForm.intersection_name,
      current_cycle: calcForm.current_cycle, phase_count: calcForm.phase_count,
      lost_time_per_phase: calcForm.lost_time, total_flow: calcForm.total_flow, saturation_flow: calcForm.saturation_flow,
    })
    calcResult.value = res.data?.data || res.data || {}
    ElMessage.success('Webster配时计算完成'); fetchStats(); fetchHistory()
  } catch (e) { ElMessage.error(e?.response?.data?.message || '计算失败') }
  finally { calcLoading.value = false }
}

async function doApply(optId) {
  applyLoading.value = true
  try { await signalApi.apply(optId); ElMessage.success('配时方案已应用'); fetchStats(); fetchHistory() }
  catch { ElMessage.error('应用失败') }
  finally { applyLoading.value = false }
}

function formatTime(iso) { if (!iso) return ''; try { return iso.replace('T', ' ').slice(0, 19) } catch { return iso } }

onMounted(async () => { await Promise.all([fetchIntersections(), fetchStats(), fetchHistory()]) })
</script>

<style scoped>
.signal-view { max-width: 1400px; }
.signal-header-stats { display: flex; gap: 24px; margin-bottom: 12px; }
.signal-stat-card { text-align: center; }
.ss-num { font-size: 28px; font-weight: 700; }
.ss-label { font-size: 12px; color: var(--text-secondary); margin-top: 2px; display: block; }
.signal-grid { display: grid; grid-template-columns: 380px 1fr; gap: 12px; }
@media (max-width: 960px) { .signal-grid { grid-template-columns: 1fr; } }
.signal-card { background: var(--bg-panel); }
.signal-right { display: flex; flex-direction: column; gap: 12px; }
.card-title { font-weight: 600; color: var(--text-primary); }
.result-card { border: 1px solid rgba(0,212,255,.15); }
.result-grid { display: flex; gap: 16px; justify-content: center; margin-bottom: 12px; }
.result-item { text-align: center; }
.result-val { font-size: 26px; font-weight: 700; }
.result-lbl { font-size: 11px; color: var(--text-secondary); margin-top: 2px; }
.green-splits { background: rgba(255,255,255,.02); border-radius: 8px; padding: 12px; }
.split-title { font-size: 13px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px; }
.split-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 12px; color: var(--text-secondary); }
.split-bar { flex: 1; height: 8px; background: rgba(255,255,255,.08); border-radius: 4px; overflow: hidden; }
.split-fill { height: 100%; background: linear-gradient(90deg, #00d4ff, #4caf50); border-radius: 4px; transition: width .5s; }
</style>
