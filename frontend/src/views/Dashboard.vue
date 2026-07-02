<template>
  <div>
    <h2 style="color:var(--text-primary);margin-bottom:24px">系统首页</h2>
    <el-row :gutter="20">
      <el-col :span="6" v-for="card in statsCards" :key="card.title">
        <div class="stat-card">
          <div class="stat-icon" :style="{background:card.color}">{{ card.icon }}</div>
          <div class="stat-info">
            <div class="stat-value">{{ card.value }}</div>
            <div class="stat-title">{{ card.title }}</div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { statsApi } from '@/api/stats'
const statsCards = ref([
  { icon:'🛣️', title:'路段总数', value:0,   color:'linear-gradient(135deg,#00d4ff,#0099cc)' },
  { icon:'📡', title:'检测器数', value:0,   color:'linear-gradient(135deg,#00e676,#00b248)' },
  { icon:'⚠️', title:'今日预警', value:0,   color:'linear-gradient(135deg,#ff9800,#f57c00)' },
  { icon:'📈', title:'预测精度(RF)', value:'--', color:'linear-gradient(135deg,#ab47bc,#7b1fa2)' },
])
onMounted(async () => {
  try {
    const res = await statsApi.getDashboard()
    const d = res.data || res
    statsCards.value[0].value = d.total_sections || 0
    statsCards.value[1].value = d.active_detectors || 0
    statsCards.value[2].value = d.today_warnings || 0
    statsCards.value[3].value = (d.avg_prediction_accuracy || 0) + '%'
  } catch {}
})
</script>

<style scoped>
.stat-card {
  background: var(--bg-panel); border-radius: 12px; padding: 24px;
  display: flex; align-items: center; gap: 16px;
  transition: transform .2s, box-shadow .2s; cursor: default;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 20px rgba(0,212,255,.15); }
.stat-icon { width: 52px; height: 52px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; flex-shrink: 0; }
.stat-value { font-size: 28px; font-weight: bold; color: var(--text-primary); }
.stat-title { font-size: 13px; color: var(--text-secondary); margin-top: 2px; }
</style>
