<template>
  <div style="color:var(--text-primary)">
    <h2>流量预测看板</h2>
    <el-row :gutter="20" style="margin-bottom:16px">
      <el-col :span="8"><el-select v-model="sectionId" placeholder="选择路段" style="width:100%"><el-option v-for="s in sections" :key="s.id" :label="s.name" :value="s.id" /></el-select></el-col>
      <el-col :span="8"><el-select v-model="model" style="width:100%"><el-option label="随机森林(RF)" value="RF" /><el-option label="KNN回归" value="KNN" /></el-select></el-col>
      <el-col :span="8"><el-button type="primary" @click="fetchPrediction" :loading="loading">预测</el-button></el-col>
    </el-row>
    <el-card v-if="result" style="background:var(--bg-panel);margin-bottom:16px">
      <div style="font-size:32px;font-weight:bold;color:var(--accent-blue)">{{ result.predicted_flow }} <span style="font-size:14px">veh/h</span></div>
      <div style="color:var(--text-secondary)">置信区间: {{ result.confidence_interval.lower }} ~ {{ result.confidence_interval.upper }}</div>
    </el-card>
    <el-card style="background:var(--bg-panel)"><div ref="chartRef" style="height:300px"></div></el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { predictionApi } from '@/api/prediction'
const sections = ref([]); const sectionId = ref(null); const model = ref('RF')
const loading = ref(false); const result = ref(null); const chartRef = ref(null)
const fetchPrediction = async () => {
  if (!sectionId.value) return
  loading.value = true
  try { const res = await predictionApi.getForecast(sectionId.value, 15, model.value); result.value = res.data }
  finally { loading.value = false }
}
onMounted(() => { /* TODO: 加载sections列表 + ECharts渲染 */ })
</script>
