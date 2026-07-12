<template>
  <div class="scenarios-view">
    <div class="page-header">
      <h2>场景仿真</h2>
      <el-button type="primary" @click="showCreate = true">新建场景</el-button>
    </div>

    <!-- 场景列表 -->
    <el-card class="list-card" v-loading="loading">
      <el-table :data="scenarios" stripe size="small" style="width:100%">
        <el-table-column prop="name" label="场景名称" min-width="160" />
        <el-table-column label="干预类型" width="120">
          <template #default="{ row }">{{ interventionLabel(row.intervention_type) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small" effect="dark">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="improvement_pct" label="改善率" width="100">
          <template #default="{ row }">
            <span v-if="row.improvement_pct != null">{{ row.improvement_pct }}%</span>
            <span v-else>--</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">{{ formatTs(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleView(row)" :disabled="row.status !== 'completed'">查看</el-button>
            <el-button size="small" type="primary" @click="handleRun(row)" :loading="row._running" :disabled="row.status === 'running' || row.status === 'pending'">
              {{ row.status === 'completed' ? '重新运行' : '运行' }}
            </el-button>
            <el-popconfirm title="确认删除？" @confirm="handleDelete(row)">
              <template #reference>
                <el-button size="small" type="danger" text>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap" v-if="total > pageSize">
        <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" small @current-change="loadScenarios" />
      </div>
    </el-card>

    <!-- 结果对比视图 -->
    <el-card class="result-card" v-if="resultData" v-loading="resultLoading">
      <template #header>
        <span>仿真结果：{{ resultData.scenario_name || currentScenario?.name }}</span>
        <div class="result-actions">
          <el-button size="small" @click="handleExportReport">导出报告</el-button>
          <el-button size="small" type="warning" @click="handleSendAdmin">发送管理员</el-button>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col :span="8" v-for="(col, ci) in comparisonCols" :key="ci">
          <el-card class="compare-card" :class="`compare-${ci}`">
            <template #header>
              <strong>{{ col.label }}</strong>
              <el-tag v-if="ci === 2 && resultData.delta" type="success" size="small" effect="dark" style="margin-left:8px">
                {{ formatDelta(resultData.delta) }}
              </el-tag>
            </template>
            <div class="compare-metrics">
              <div class="cmp-item">
                <span class="cmp-label">总延误</span>
                <span class="cmp-value">{{ col.data.total_delay_veh_h }} veh·h</span>
              </div>
              <div class="cmp-item">
                <span class="cmp-label">平均速度</span>
                <span class="cmp-value">{{ col.data.avg_speed_kmh }} km/h</span>
              </div>
              <div class="cmp-item">
                <span class="cmp-label">拥堵路段</span>
                <span class="cmp-value">{{ col.data.num_congested }} / {{ col.data.num_segments }}</span>
              </div>
              <div class="cmp-item">
                <span class="cmp-label">CO₂排放</span>
                <span class="cmp-value">{{ col.data.total_co2_kg }} kg/h</span>
              </div>
              <div class="cmp-item">
                <span class="cmp-label">拥堵率</span>
                <span class="cmp-value">{{ col.data.congestion_ratio }}%</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- 新建场景对话框 -->
    <el-dialog v-model="showCreate" title="新建场景" width="500px" destroy-on-close>
      <el-form :model="createForm" label-position="top" size="small">
        <el-form-item label="场景名称" required>
          <el-input v-model="createForm.name" placeholder="请输入场景名称" />
        </el-form-item>
        <el-form-item label="干预类型" required>
          <el-select v-model="createForm.intervention_type" style="width:100%">
            <el-option label="限流" value="flow_limit" />
            <el-option label="信号优化" value="signal_optimize" />
            <el-option label="路段封闭" value="road_closure" />
            <el-option label="组合策略" value="combined" />
          </el-select>
        </el-form-item>
        <el-form-item label="参数" v-if="createForm.intervention_type === 'flow_limit'">
          <el-slider v-model="createForm.limit_pct" :min="5" :max="50" :step="5" show-stops />
        </el-form-item>
        <el-form-item label="信号效率提升 (%)" v-if="createForm.intervention_type === 'signal_optimize'">
          <el-slider v-model="createForm.efficiency_gain" :min="5" :max="30" :step="5" show-stops />
        </el-form-item>
        <el-form-item label="仿真时长">
          <el-select v-model="createForm.duration" style="width:100%">
            <el-option label="5 分钟" :value="300" />
            <el-option label="15 分钟" :value="900" />
            <el-option label="30 分钟" :value="1800" />
            <el-option label="60 分钟" :value="3600" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">创建并运行</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { scenarioApi } from '@/api/scenario'

const scenarios = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const loading = ref(false)
const creating = ref(false)
const resultLoading = ref(false)
const showCreate = ref(false)
const resultData = ref(null)
const currentScenario = ref(null)

const createForm = reactive({
  name: '',
  intervention_type: 'flow_limit',
  limit_pct: 20,
  efficiency_gain: 15,
  duration: 900,
})

const comparisonCols = ref([])

function interventionLabel(type) {
  const map = { flow_limit: '限流', signal_optimize: '信号优化', road_closure: '路段封闭', combined: '组合策略' }
  return map[type] || type
}

function statusType(s) {
  const map = { pending: 'info', running: 'warning', completed: 'success', failed: 'danger' }
  return map[s] || 'info'
}

function statusLabel(s) {
  const map = { pending: '待运行', running: '运行中', completed: '已完成', failed: '失败' }
  return map[s] || s
}

function formatDelta(delta) {
  if (!delta) return ''
  const parts = []
  if (delta.delay_reduction_pct) parts.push(`延误-${delta.delay_reduction_pct}%`)
  if (delta.speed_increase_kmh && delta.speed_increase_kmh > 0) parts.push(`速度+${delta.speed_increase_kmh}km/h`)
  if (delta.co2_reduction_pct) parts.push(`CO₂-${delta.co2_reduction_pct}%`)
  return parts.join(' / ')
}

function formatTs(ts) {
  if (!ts) return '--'
  try { return new Date(ts).toLocaleString('zh-CN') } catch { return ts }
}

async function loadScenarios() {
  loading.value = true
  try {
    const res = await scenarioApi.list({ page: page.value, page_size: pageSize })
    const data = res.data || res
    scenarios.value = (data.items || []).map(s => ({ ...s, _running: false }))
    total.value = data.total || 0
  } catch { scenarios.value = [] }
  loading.value = false
}

async function handleRun(scenario) {
  scenario._running = true
  try {
    const res = await scenarioApi.run(scenario.id)
    const data = res.data || res
    // update scenario status
    scenario.status = 'completed'
    scenario.improvement_pct = data.improvement_pct
    // show result
    currentScenario.value = scenario
    buildComparisonView(data)
  } catch {
    scenario.status = 'failed'
  }
  scenario._running = false
}

function buildComparisonView(data) {
  if (!data) return
  const baseline = data.baseline || {}
  const intervention = data.intervention || {}
  const delta = data.delta || {}

  resultData.value = {
    scenario_name: currentScenario.value?.name,
    delta,
  }
  comparisonCols.value = [
    { label: '现状（基线）', data: baseline },
    { label: '干预后', data: intervention },
    { label: '改善效果', data: delta },
  ]
}

async function handleView(scenario) {
  currentScenario.value = scenario
  resultLoading.value = true
  try {
    const res = await scenarioApi.get(scenario.id)
    const data = res.data || res
    // parse result from stored data
    const baseStr = data.baseline_result || data.baseline_result_json
    const intStr = data.intervention_result || data.intervention_result_json
    if (baseStr && intStr) {
      let baseline, intervention
      try { baseline = typeof baseStr === 'string' ? JSON.parse(baseStr) : baseStr } catch { baseline = {} }
      try { intervention = typeof intStr === 'string' ? JSON.parse(intStr) : intStr } catch { intervention = {} }
      buildComparisonView({ baseline, intervention, improvement_pct: data.improvement_pct })
    } else {
      resultData.value = null
      comparisonCols.value = []
    }
  } catch {
    resultData.value = null
    comparisonCols.value = []
  }
  resultLoading.value = false
}

async function handleDelete(scenario) {
  try {
    await scenarioApi.delete(scenario.id)
    scenarios.value = scenarios.value.filter(s => s.id !== scenario.id)
  } catch { /* ignore */ }
}

async function handleCreate() {
  if (!createForm.name) return
  creating.value = true
  try {
    const params = {}
    if (createForm.intervention_type === 'flow_limit') params.limit_pct = createForm.limit_pct
    if (createForm.intervention_type === 'signal_optimize') params.efficiency_gain = createForm.efficiency_gain
    params.duration = createForm.duration

    const res = await scenarioApi.create({
      name: createForm.name,
      intervention_type: createForm.intervention_type,
      params,
    })
    showCreate.value = false
    // reload list and run newly created scenario
    await loadScenarios()
    const data = res.data || res
    if (data?.id) {
      const newSc = scenarios.value.find(s => s.id === data.id)
      if (newSc) await handleRun(newSc)
    }
  } catch { /* ignore */ }
  creating.value = false
}

function handleExportReport() {
  if (!resultData.value) return
  const rows = comparisonCols.value.map(col => {
    const d = col.data
    return `${col.label},${d.total_delay_veh_h || 0},${d.avg_speed_kmh || 0},${d.num_congested || 0}/${d.num_segments || 0},${d.total_co2_kg || 0},${d.congestion_ratio || 0}%`
  })
  const csv = '场景,总延误(veh·h),平均速度(km/h),拥堵路段,CO₂排放(kg/h),拥堵率\n' + rows.join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `scenario_${currentScenario.value?.name || 'result'}_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(link.href)
}

function handleSendAdmin() {
  // Placeholder: would call backend notification API
  alert('已通知管理员审核该场景仿真结果（演示功能）')
}

onMounted(loadScenarios)
</script>

<style scoped>
.scenarios-view { padding: 0; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.page-header h2 { color: var(--text-primary); margin: 0; font-size: 20px; }

.list-card { background: var(--bg-panel); border: 1px solid rgba(255,255,255,0.06); margin-bottom: 20px; }
.list-card :deep(.el-table) { background: transparent; }
.list-card :deep(.el-table tr) { background: transparent; }
.list-card :deep(.el-table th.el-table__cell) { background: rgba(255,255,255,0.03); }
.list-card :deep(.el-table td) { background: transparent; }
.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }

.result-card { background: var(--bg-panel); border: 1px solid rgba(255,255,255,0.06); }
.result-card :deep(.el-card__header) { display: flex; align-items: center; justify-content: space-between; }
.result-actions { display: flex; gap: 8px; }

.compare-card { background: transparent; border: 1px solid rgba(255,255,255,0.08); }
.compare-card :deep(.el-card__header) {
  border-bottom: 1px solid rgba(255,255,255,0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.compare-0 { border-color: rgba(100, 181, 246, 0.3); }
.compare-1 { border-color: rgba(255, 183, 77, 0.3); }
.compare-2 { border-color: rgba(129, 199, 132, 0.3); }

.compare-metrics { display: flex; flex-direction: column; gap: 12px; }
.cmp-item { display: flex; justify-content: space-between; align-items: center; }
.cmp-label { font-size: 13px; color: var(--text-secondary); }
.cmp-value { font-size: 15px; font-weight: 600; color: var(--text-primary); font-variant-numeric: tabular-nums; }
</style>
