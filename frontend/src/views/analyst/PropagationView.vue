<template>
  <div class="propagation-view">
    <h2>拥堵传播分析</h2>

    <el-row :gutter="20">
      <!-- 左侧控制面板 -->
      <el-col :span="6">
        <el-card class="control-card">
          <template #header>分析参数</template>
          <el-form label-position="top" size="small">
            <el-form-item label="起始路段">
              <el-select v-model="form.section_id" filterable placeholder="搜索路段..." style="width:100%">
                <el-option v-for="s in sections" :key="s.id" :label="s.name" :value="s.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="传播步数">
              <el-slider v-model="form.max_depth" :min="1" :max="5" :step="1" show-stops />
            </el-form-item>
            <el-form-item label="时间窗口（分钟）">
              <el-select v-model="form.time_window" style="width:100%">
                <el-option :label="'15 分钟'" :value="15" />
                <el-option :label="'30 分钟'" :value="30" />
                <el-option :label="'60 分钟'" :value="60" />
              </el-select>
            </el-form-item>
            <el-form-item label="置信度阈值">
              <el-slider v-model="form.min_probability" :min="0.5" :max="0.9" :step="0.05" show-stops />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleAnalyze" :loading="analyzing" style="width:100%">
                执行分析
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右侧传播树 + 表格 -->
      <el-col :span="18">
        <el-card class="tree-card" v-loading="analyzing">
          <template #header>
            <span>拥堵传播树</span>
            <span class="tree-stats" v-if="treeData">
              节点: {{ treeData.total_nodes }} | 最大深度: {{ treeData.max_depth }}
            </span>
          </template>
          <div ref="treeChartRef" class="tree-chart" v-if="treeData"></div>
          <el-empty v-else description="请选择路段并点击「执行分析」" :image-size="80" />
        </el-card>

        <!-- 传播链数据表格 -->
        <el-card class="table-card" v-if="flatList.length > 0">
          <template #header>传播链详情</template>
          <el-table :data="flatList" stripe size="small" style="width:100%">
            <el-table-column prop="from" label="源路段" min-width="100" />
            <el-table-column prop="to" label="目标路段" min-width="100" />
            <el-table-column label="传播概率" width="120">
              <template #default="{ row }">
                <el-tag :type="probType(row.probability)" size="small">
                  {{ (row.probability * 100).toFixed(1) }}%
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="delay_minutes" label="延迟（分钟）" width="120" />
            <el-table-column prop="depth" label="深度" width="80" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { sectionsApi } from '@/api/sections'
import { propagationApi } from '@/api/propagation'
import * as echarts from 'echarts/core'
import { TreeChart } from 'echarts/charts'
import { TooltipComponent, GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([TreeChart, TooltipComponent, GridComponent, CanvasRenderer])

const sections = ref([])
const analyzing = ref(false)
const treeData = ref(null)
const flatList = ref([])
const treeChartRef = ref(null)
let treeChart = null

const form = reactive({
  section_id: null,
  max_depth: 3,
  time_window: 30,
  min_probability: 0.5,
})

function probType(p) {
  if (p >= 0.7) return 'danger'
  if (p >= 0.5) return 'warning'
  return 'info'
}

async function loadSections() {
  try {
    const res = await sectionsApi.getList()
    const data = res.data || res
    sections.value = data.items || data || []
    if (sections.value.length > 0 && !form.section_id) {
      form.section_id = sections.value[0].id
    }
  } catch { /* keep empty */ }
}

async function handleAnalyze() {
  if (!form.section_id) return
  analyzing.value = true
  try {
    const res = await propagationApi.analyze({
      section_id: form.section_id,
      max_depth: form.max_depth,
      time_window: form.time_window,
      min_probability: form.min_probability,
    })
    treeData.value = res.data || res
    flatList.value = treeData.value?.flat_list || extractFlat(treeData.value?.propagation_tree)
    await nextTick()
    renderTreeChart()
  } catch {
    treeData.value = null
    flatList.value = []
  }
  analyzing.value = false
}

function extractFlat(tree) {
  if (!tree) return []
  const result = []
  function dfs(node) {
    if (node.from) {
      result.push({
        from: node.from,
        to: node.section_id,
        probability: node.probability,
        delay_minutes: node.delay_minutes,
        depth: node.depth,
      })
    }
    ;(node.children || []).forEach(dfs)
  }
  dfs(tree)
  return result
}

function buildEChartsTree(node) {
  if (!node) return null
  const label = `${node.section_id}\nP=${(node.probability * 100).toFixed(0)}%`
  const color = node.probability >= 0.7 ? '#f44336' : node.probability >= 0.5 ? '#ff9800' : '#ffeb3b'
  return {
    name: label,
    value: node.section_id,
    itemStyle: { color },
    children: (node.children || []).map(buildEChartsTree).filter(Boolean),
  }
}

function renderTreeChart() {
  if (!treeChartRef.value || !treeData.value) return
  if (!treeChart) treeChart = echarts.init(treeChartRef.value)

  const root = treeData.value.propagation_tree || treeData.value
  const treeRoot = buildEChartsTree(root)

  if (!treeRoot) return

  // find section name for root
  const sec = sections.value.find(s => s.id === Number(root.section_id) || s.id === root.section_id)
  treeRoot.name = `${sec?.name || root.section_id}\n${treeRoot.name}`

  treeChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const lines = params.name.split('\n')
        return `<strong>路段: ${lines[0]}</strong><br/>${lines.slice(1).join('<br/>')}`
      },
    },
    series: [{
      type: 'tree',
      data: [treeRoot],
      top: '5%',
      left: '10%',
      bottom: '5%',
      right: '20%',
      symbolSize: 10,
      orient: 'LR',
      expandAndCollapse: true,
      initialTreeDepth: 3,
      label: {
        position: 'right',
        verticalAlign: 'middle',
        align: 'left',
        fontSize: 12,
        color: '#ccc',
      },
      leaves: { label: { position: 'right', align: 'left' } },
      lineStyle: { color: '#555', width: 1.5 },
    }],
  })
}

onMounted(async () => {
  await loadSections()
})

onUnmounted(() => {
  treeChart?.dispose()
})
</script>

<style scoped>
.propagation-view { padding: 0; }
.propagation-view h2 { color: var(--text-primary); margin: 0 0 20px; font-size: 20px; }

.control-card { background: var(--bg-panel); border: 1px solid rgba(255,255,255,0.06); }
.tree-card { background: var(--bg-panel); border: 1px solid rgba(255,255,255,0.06); margin-bottom: 16px; }
.tree-card :deep(.el-card__header) { display: flex; align-items: center; justify-content: space-between; }
.tree-stats { font-size: 12px; color: var(--text-secondary); }
.tree-chart { height: 420px; }

.table-card { background: var(--bg-panel); border: 1px solid rgba(255,255,255,0.06); }
.table-card :deep(.el-table) { background: transparent; }
.table-card :deep(.el-table tr) { background: transparent; }
.table-card :deep(.el-table td) { background: transparent; }
</style>
