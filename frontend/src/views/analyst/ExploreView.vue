<template>
  <div class="explore-view">
    <h2>数据探索</h2>

    <!-- 查询面板 -->
    <el-card class="query-card">
      <el-form :model="query" inline size="small" label-width="80">
        <el-form-item label="日期范围">
          <el-date-picker v-model="query.dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" style="width:240px" />
        </el-form-item>
        <el-form-item label="路段">
          <el-select v-model="query.section_id" filterable placeholder="全部路段" clearable style="width:150px">
            <el-option v-for="s in sections" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="小时范围">
          <el-select v-model="query.hourStart" placeholder="起始" style="width:100px">
            <el-option v-for="h in 24" :key="h-1" :label="`${String(h-1).padStart(2,'0')}:00`" :value="h-1" />
          </el-select>
          <span style="margin:0 8px;color:var(--text-secondary)">至</span>
          <el-select v-model="query.hourEnd" placeholder="结束" style="width:100px">
            <el-option v-for="h in 24" :key="h-1" :label="`${String(h-1).padStart(2,'0')}:00`" :value="h-1" />
          </el-select>
        </el-form-item>
        <el-form-item label="星期">
          <el-checkbox-group v-model="query.weekdays">
            <el-checkbox v-for="(d, i) in weekNames" :key="i" :label="i" size="small">{{ d }}</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch" :loading="searching">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button @click="handleExport" :disabled="!records.length">导出CSV</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据统计 -->
    <el-row :gutter="16" class="stats-row" v-if="records.length">
      <el-col :span="6">
        <el-card class="mini-stat">
          <div class="mini-val">{{ totalCount }}</div>
          <div class="mini-lbl">记录数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="mini-stat">
          <div class="mini-val">{{ avgFlow.toFixed(1) }}</div>
          <div class="mini-lbl">平均流量 (veh)</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="mini-stat">
          <div class="mini-val">{{ avgSpeed.toFixed(1) }}</div>
          <div class="mini-lbl">平均速度 (km/h)</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="mini-stat">
          <div class="mini-val">{{ anomalyCount }}</div>
          <div class="mini-lbl">异常数据点</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table :data="pagedRecords" stripe size="small" style="width:100%" height="460" v-loading="searching">
        <el-table-column type="index" width="50" />
        <el-table-column prop="timestamp" label="时间" width="160">
          <template #default="{ row }">{{ formatTs(row.timestamp) }}</template>
        </el-table-column>
        <el-table-column prop="section_name" label="路段" min-width="120" />
        <el-table-column prop="vehicle_count" label="流量 (veh)" width="100" />
        <el-table-column prop="avg_speed" label="速度 (km/h)" width="100">
          <template #default="{ row }">
            <span :class="isAnomaly(row) ? 'anomaly' : ''">{{ row.avg_speed }}</span>
          </template>
        </el-table-column>
        <el-table-column label="拥堵等级" width="100">
          <template #default="{ row }">
            <TrafficBadge :occupancy="levelToOccupancy(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="occupancy" label="占有率" width="80" />
        <el-table-column label="异常" width="70">
          <template #default="{ row }">
            <el-tag v-if="isAnomaly(row)" type="warning" size="small" effect="dark">异常</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap" v-if="records.length > 0">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="records.length"
          layout="total, prev, pager, next"
          small
        />
      </div>
    </el-card>

    <el-empty v-if="!searching && !records.length" description="暂无数据，请设置查询条件后点击查询" :image-size="80" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { sectionsApi } from '@/api/sections'
import { trafficApi } from '@/api/traffic'
import TrafficBadge from '@/components/common/TrafficBadge.vue'

const weekNames = ['日', '一', '二', '三', '四', '五', '六']

const sections = ref([])
const records = ref([])
const searching = ref(false)
const page = ref(1)
const pageSize = 20

const query = reactive({
  dateRange: null,
  section_id: null,
  hourStart: null,
  hourEnd: null,
  weekdays: [],
})

const pagedRecords = computed(() => {
  const start = (page.value - 1) * pageSize
  return records.value.slice(start, start + pageSize)
})

const totalCount = computed(() => records.value.length)
const avgFlow = computed(() => {
  if (!records.value.length) return 0
  return records.value.reduce((s, r) => s + (r.vehicle_count || 0), 0) / records.value.length
})
const avgSpeed = computed(() => {
  if (!records.value.length) return 0
  return records.value.reduce((s, r) => s + (r.avg_speed || 0), 0) / records.value.length
})
const anomalyCount = computed(() => records.value.filter(isAnomaly).length)

function isAnomaly(row) {
  return (row.avg_speed && row.avg_speed > 80) || (row.avg_speed && row.avg_speed < 5 && row.vehicle_count > 0)
}

function levelToOccupancy(row) {
  // map avg_speed to approximate occupancy for badge
  if (!row.avg_speed) return 0
  if (row.avg_speed > 50) return 15
  if (row.avg_speed > 35) return 40
  if (row.avg_speed > 20) return 65
  return 90
}

function formatTs(ts) {
  if (!ts) return '--'
  try { return new Date(ts).toLocaleString('zh-CN') } catch { return ts }
}

async function loadSections() {
  try {
    const res = await sectionsApi.getList()
    const data = res.data || res
    sections.value = data.items || data || []
  } catch { /* keep empty */ }
}

async function handleSearch() {
  searching.value = true
  page.value = 1
  try {
    const params = {}
    if (query.section_id) params.section_id = query.section_id
    if (query.dateRange && query.dateRange.length === 2) {
      params.start = `${query.dateRange[0]}T00:00:00`
      params.end = `${query.dateRange[1]}T23:59:59`
    }
    if (query.hourStart != null) params.hour_start = query.hourStart
    if (query.hourEnd != null) params.hour_end = query.hourEnd
    if (query.weekdays.length) params.weekdays = query.weekdays.join(',')

    const res = await trafficApi.getHistory(params)
    const data = res.data || res
    records.value = data.items || data || []

    // enrich section names
    if (records.value.length && sections.value.length) {
      const secMap = Object.fromEntries(sections.value.map(s => [s.id, s.name]))
      records.value.forEach(r => {
        if (!r.section_name) r.section_name = secMap[r.section_id] || `路段${r.section_id}`
      })
    }
  } catch { records.value = [] }
  searching.value = false
}

function handleReset() {
  query.dateRange = null
  query.section_id = null
  query.hourStart = null
  query.hourEnd = null
  query.weekdays = []
  records.value = []
  page.value = 1
}

function handleExport() {
  if (!records.value.length) return
  const headers = ['时间', '路段', '流量(veh)', '速度(km/h)', '占有率(%)', '路段ID']
  const rows = records.value.map(r => [
    formatTs(r.timestamp),
    r.section_name || `路段${r.section_id}`,
    r.vehicle_count,
    r.avg_speed,
    r.occupancy,
    r.section_id,
  ])
  const csv = [headers.join(','), ...rows.map(row => row.join(','))].join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `traffic_data_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(link.href)
}

onMounted(loadSections)
</script>

<style scoped>
.explore-view { padding: 0; }
.explore-view h2 { color: var(--text-primary); margin: 0 0 20px; font-size: 20px; }

.query-card { background: var(--bg-panel); border: 1px solid rgba(255,255,255,0.06); margin-bottom: 16px; }
.query-card :deep(.el-form-item) { margin-bottom: 8px; }
.query-card :deep(.el-form-item__label) { color: var(--text-secondary); }

.stats-row { margin-bottom: 16px; }
.mini-stat { background: var(--bg-panel); border: 1px solid rgba(255,255,255,0.06); text-align: center; padding: 10px 0; }
.mini-val { font-size: 22px; font-weight: 700; color: var(--text-primary); font-variant-numeric: tabular-nums; }
.mini-lbl { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }

.table-card { background: var(--bg-panel); border: 1px solid rgba(255,255,255,0.06); }
.table-card :deep(.el-table) { background: transparent; }
.table-card :deep(.el-table tr) { background: transparent; }
.table-card :deep(.el-table th.el-table__cell) { background: rgba(255,255,255,0.03); }
.table-card :deep(.el-table td) { background: transparent; }

.anomaly { color: #ff9800; font-weight: 700; }

.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
