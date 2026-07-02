<template>
  <div>
    <h2 style="color:var(--text-primary)">系统首页</h2>
    <el-row :gutter="20">
      <el-col :span="6" v-for="card in statsCards" :key="card.title">
        <el-card style="background:var(--bg-panel);color:var(--text-primary);margin-bottom:16px">
          <div style="font-size:28px;font-weight:bold">{{ card.value }}</div>
          <div style="color:var(--text-secondary)">{{ card.title }}</div>
        </el-card>
      </el-col>
    </el-row>
    <el-card style="background:var(--bg-panel);color:var(--text-primary)">
      <div ref="chartRef" style="height:300px"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const statsCards = [
  { title: '路段总数', value: 24 },
  { title: '检测器数', value: 40 },
  { title: '今日预警', value: 0 },
  { title: '预测精度(RF)', value: '85%' },
]
const chartRef = ref(null)
// TODO D8: 接入statsApi.getDashboard()渲染ECharts趋势图
onMounted(() => { /* ECharts init pending */ })
</script>
