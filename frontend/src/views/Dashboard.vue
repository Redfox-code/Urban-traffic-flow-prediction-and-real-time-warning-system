<template>
  <div>
    <h2 style="color:var(--text-primary)">系统首页</h2>
    <el-row :gutter="20">
      <el-col :span="6" v-for="card in statsCards" :key="card.title">
        <el-card style="background:var(--bg-panel);color:var(--text-primary);margin-bottom:16px">
          <div style="font-size:28px;font-weight:bold;color:var(--accent-blue)">{{ card.value }}</div>
          <div style="color:var(--text-secondary)">{{ card.title }}</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { statsApi } from '@/api/stats'
const statsCards = ref([
  { title: '路段总数', value: 0 }, { title: '检测器数', value: 0 },
  { title: '今日预警', value: 0 }, { title: '预测精度(RF)', value: '--' },
])
onMounted(async () => {
  try {
    const res = await statsApi.getDashboard()
    const d = res.data || res
    statsCards.value[0].value = d.total_sections || 0
    statsCards.value[1].value = d.active_detectors || 0
    statsCards.value[2].value = d.today_warnings || 0
    statsCards.value[3].value = (d.avg_prediction_accuracy || 0) + '%'
  } catch (e) { console.warn('Dashboard load failed:', e.message) }
})
</script>
