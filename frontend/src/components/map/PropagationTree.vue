<template>
  <div class="propagation-tree">
    <div class="pt-header">
      <span class="pt-title">拥堵传播树</span>
      <el-tag v-if="rootName" size="small" effect="dark" type="danger">{{ rootName }}</el-tag>
    </div>
    <div ref="treeContainer" class="pt-chart"></div>
    <div class="pt-legend">
      <div class="pt-legend-item"><span class="pt-dot" style="background:var(--traffic-smooth)"></span>畅通</div>
      <div class="pt-legend-item"><span class="pt-dot" style="background:var(--traffic-slow)"></span>缓行</div>
      <div class="pt-legend-item"><span class="pt-dot" style="background:var(--traffic-congested)"></span>拥堵</div>
      <div class="pt-legend-item"><span class="pt-dot" style="background:var(--traffic-jammed)"></span>严重</div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Object, default: null },
  // ECharts Tree格式: {name, itemStyle:{color}, children:[...]}
  // 或者扁平格式: {rootName, segments:[], children:[{name, probability, delay, level, children}]}
  rootName: { type: String, default: '' },
  height: { type: String, default: '300px' },
})

const treeContainer = ref(null)
let chartInstance = null

// 将传播数据转换为ECharts Tree格式
const toTreeData = () => {
  if (props.data?.name) {
    // 已经是ECharts格式
    return transformNode(props.data)
  }
  if (props.data?.children) {
    return {
      name: props.data.rootName || '拥堵源',
      children: props.data.children.map(child => transformNode(child)),
    }
  }
  // 没有数据时返回占位
  return { name: '无传播数据', children: [] }
}

const transformNode = (node) => {
  if (!node) return { name: '?', children: [] }
  const levelColors = {
    jammed: '#f5222d', congested: '#fa8c16', slow: '#fadb14', smooth: '#52c41a',
  }
  const color = levelColors[node.level] || '#8899aa'
  const label = `${node.name}\n${node.delay ? node.delay + 's' : ''}${node.probability ? ' · ' + Math.round(node.probability * 100) + '%' : ''}`
  return {
    name: label,
    itemStyle: { color },
    lineStyle: node.probability ? { opacity: 0.3 + node.probability * 0.7 } : undefined,
    children: node.children ? node.children.map(c => transformNode(c)) : [],
  }
}

const renderChart = () => {
  if (!treeContainer.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(treeContainer.value)
  }

  const treeData = toTreeData()

  chartInstance.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      triggerOn: 'mousemove',
      formatter: (params) => {
        const lines = params.name.split('\n')
        return `<div style="color:#e0e6ed">${lines[0]}</div>${lines[1] ? '<div style="color:#8899aa;font-size:12px">' + lines[1] + '</div>' : ''}`
      },
    },
    series: [{
      type: 'tree',
      data: [treeData],
      top: '5%',
      left: '5%',
      bottom: '5%',
      right: '15%',
      symbol: 'circle',
      symbolSize: 10,
      orient: 'LR',
      expandAndCollapse: true,
      label: {
        position: 'right',
        offset: [8, 0],
        fontSize: 12,
        color: '#e0e6ed',
        formatter: (params) => params.name.split('\n')[0],
      },
      leaves: { label: { position: 'right' } },
      lineStyle: { color: 'rgba(255,255,255,.2)', width: 2 },
      itemStyle: {
        borderColor: 'rgba(255,255,255,.15)',
        borderWidth: 1,
      },
    }],
  })
}

watch(() => props.data, () => { nextTick(renderChart) }, { deep: true })

onMounted(() => { nextTick(renderChart) })

onUnmounted(() => {
  chartInstance?.dispose()
  chartInstance = null
})

defineExpose({ renderChart })
</script>

<style scoped>
.propagation-tree {
  background: var(--bg-panel);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 12px;
  overflow: hidden;
}
.pt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  border-bottom: 1px solid rgba(255,255,255,.06);
}
.pt-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.pt-chart {
  width: 100%;
  height: v-bind(height);
}
.pt-legend {
  display: flex;
  gap: 12px;
  padding: 8px 14px;
  border-top: 1px solid rgba(255,255,255,.06);
  flex-wrap: wrap;
}
.pt-legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text-secondary);
}
.pt-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
</style>
