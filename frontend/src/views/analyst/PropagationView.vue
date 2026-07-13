<template>
  <div class="propagation-view">
    <h2>拥堵传播分析</h2>
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="control-card">
          <template #header>分析参数</template>
          <el-form label-position="top" size="small">
            <el-form-item label="起始路段">
              <el-select v-model="form.section_id" filterable placeholder="搜索..." style="width:100%">
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
              <el-slider v-model="form.min_probability" :min="0.1" :max="0.6" :step="0.05" show-stops />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="doAnalyze" :loading="analyzing" style="width:100%">执行分析</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="18">
        <!-- ECharts 树图容器：inline height 保证不会被覆盖 -->
        <div ref="chartEl" style="width:100%;height:520px;background:var(--bg-panel);border:1px solid rgba(255,255,255,0.06);border-radius:8px"></div>

        <!-- 传播链表格 -->
        <el-card v-if="flatList.length" class="table-card" style="margin-top:16px">
          <template #header>传播链详情 ({{ flatList.length }} 条)</template>
          <el-table :data="flatList" stripe size="small" max-height="300">
            <el-table-column prop="from_name" label="源路段" min-width="100" />
            <el-table-column prop="to_name" label="目标路段" min-width="100" />
            <el-table-column label="传播概率" width="110">
              <template #default="{ row }">
                <el-tag :type="row.probability >= 0.7 ? 'danger' : row.probability >= 0.5 ? 'warning' : 'info'" size="small">
                  {{ (row.probability * 100).toFixed(0) }}%
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="delay_minutes" label="延迟(min)" width="90" />
            <el-table-column prop="depth" label="深度" width="60" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { sectionsApi } from '@/api/sections'
import { propagationApi } from '@/api/propagation'
import * as echarts from 'echarts'

const sections = ref([])
const analyzing = ref(false)
const treeData = ref(null)
const flatList = ref([])
const chartEl = ref(null)
let chart = null

const form = reactive({ section_id: null, max_depth: 3, time_window: 30, min_probability: 0.3 })

// ===== 初始化 =====
onMounted(async () => {
  // 并行：加载路段 + 初始化图表
  const loadSections = (async () => {
    try {
      const res = await sectionsApi.getList()
      const d = res.data || res
      sections.value = d?.items || d || []
      if (sections.value.length && !form.section_id) form.section_id = sections.value[0].id
    } catch {}
  })()

  await nextTick()
  if (chartEl.value) {
    chart = echarts.init(chartEl.value)
    window.addEventListener('resize', () => chart?.resize())
  }
  await loadSections
})

onUnmounted(() => {
  chart?.dispose()
  chart = null
})

// ===== 数据变化 → 更新图表 =====
watch(treeData, async (val) => {
  await nextTick()
  if (!chart || !val?.propagation_tree) return
  chart.setOption(buildOption(val), true)
})

// ===== 构建 ECharts option =====
function buildOption(data) {
  const root = data.propagation_tree
  const colors = ['#f44336', '#ff9800', '#4caf50', '#2196f3']
  return {
    backgroundColor: {
      type: 'linear', x: 0, y: 0, x2: 1, y2: 1,
      colorStops: [{ offset: 0, color: '#141428' }, { offset: 1, color: '#1a1a2e' }],
    },
    title: {
      text: `拥堵源: ${data.source_name}  |  ${data.total_nodes} 个节点  |  最大深度 ${data.max_depth}`,
      left: 'center', top: 10,
      textStyle: { color: '#b0b8c8', fontSize: 13, fontWeight: 'normal' },
    },
    tooltip: {
      trigger: 'item', triggerOn: 'mousemove',
      formatter: p => `<b>${p.name.split('\n')[0]}</b><br/>${p.name.split('\n').slice(1).join('<br/>')}`,
    },
    series: [{
      type: 'tree',
      data: [convertNode(root)],
      top: 48, left: 24, bottom: 16, right: 60,
      symbol: 'roundRect',
      symbolSize: [12, 12],
      orient: 'LR',
      roam: true,
      expandAndCollapse: true,
      initialTreeDepth: 4,
      edgeShape: 'curve',
      edgeForkPosition: '60%',
      label: {
        position: 'right', verticalAlign: 'middle', align: 'left',
        fontSize: 11, color: '#e0e0e0',
        backgroundColor: 'rgba(20,20,35,0.9)',
        padding: [5, 10], borderRadius: 6,
        borderWidth: 1, borderColor: 'rgba(255,255,255,0.08)',
      },
      leaves: { label: { position: 'right', verticalAlign: 'middle', align: 'left' } },
      emphasis: { focus: 'descendant', lineStyle: { color: '#00d4ff', width: 3 } },
      lineStyle: { color: 'rgba(255,255,255,0.15)', width: 1.5, curveness: 0.5 },
      itemStyle: { borderColor: 'rgba(255,255,255,0.2)', borderWidth: 2 },
    }],
  }
}

function convertNode(n) {
  if (!n) return null
  const p = n.probability || 0
  const color = p >= 0.7 ? '#f44336' : p >= 0.5 ? '#ff9800' : p >= 0.3 ? '#4caf50' : '#2196f3'
  return {
    name: (n.name || '路段' + n.section_id) + '\nP=' + (p * 100).toFixed(0) + '% | ' + (n.delay_minutes || 0).toFixed(1) + 'min',
    value: n.section_id,
    collapsed: false,
    itemStyle: { color, borderColor: color, borderWidth: 2 },
    children: (n.children || []).map(convertNode).filter(Boolean),
  }
}

// ===== 执行分析 =====
async function doAnalyze() {
  if (!form.section_id) return
  analyzing.value = true
  treeData.value = null
  flatList.value = []
  try {
    const res = await propagationApi.analyze({
      section_id: form.section_id,
      max_depth: form.max_depth,
      time_window: form.time_window,
      min_probability: form.min_probability,
    })
    treeData.value = res.data || res
    flatList.value = treeData.value?.flat_list || []
  } catch (e) { console.error(e) }
  analyzing.value = false
}
</script>

<style scoped>
.propagation-view h2 { color: var(--text-primary); margin: 0 0 20px; font-size: 20px; }
.control-card { background: var(--bg-panel); border: 1px solid rgba(255,255,255,0.06); }
.table-card { background: var(--bg-panel); border: 1px solid rgba(255,255,255,0.06); }
.table-card :deep(.el-table) { background: transparent; }
.table-card :deep(.el-table tr) { background: transparent; }
.table-card :deep(.el-table td) { background: transparent; }
</style>
