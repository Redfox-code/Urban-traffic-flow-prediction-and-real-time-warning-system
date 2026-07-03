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

    <el-card style="background:var(--bg-panel);margin-top:20px">
      <template #header><span style="font-weight:bold;color:var(--text-primary)">🔬 SUMO 仿真控制</span></template>
      <div style="display:flex;align-items:center;gap:16px">
        <el-button type="primary" @click="runSumo" :loading="sumoRunning" :disabled="sumoRunning">
          {{ sumoRunning ? '仿真运行中...' : '▶ 一键运行仿真' }}
        </el-button>
        <el-button type="success" @click="runRealtime" :loading="rtRunning" :disabled="rtRunning">
          {{ rtRunning ? '实时仿真运行中...' : '🔴 启动实时仿真' }}
        </el-button>
        <span v-if="sumoResult" :style="{color: sumoResult.includes('成功') ? '#00e676' : '#f44336'}">{{ sumoResult }}</span>
        <span v-if="sumoRunning" style="color:var(--text-secondary);font-size:13px">正在生成路网→运行仿真→导入数据库，约需1-2分钟...</span>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { statsApi } from '@/api/stats'
import request from '@/api/request'

const sumoRunning = ref(false)
const sumoResult = ref('')
const rtRunning = ref(false)

const runRealtime = async () => {
  rtRunning.value = true; sumoResult.value = ''
  try {
    const res = await request.post('/sumo/run_realtime', null, { timeout: 10000 })
    sumoResult.value = '✅ 实时仿真已启动，数据持续写入DB，请切换到实时路况页面查看'
    rtRunning.value = true  // 保持按钮禁用
  } catch (e) {
    sumoResult.value = `❌ 启动失败: ${e?.message || ''}`
    rtRunning.value = false
  }
}

const runSumo = async () => {
  sumoRunning.value = true; sumoResult.value = ''
  try {
    const res = await request.post('/sumo/run', null, { timeout: 180000 })  // 3分钟超时
    const data = res.data || res
    sumoResult.value = `✅ ${data.status || '完成'} (导入${data.records_imported || 0}条记录)`
    ElMessage.success('仿真完成，数据已导入')
  } catch (e) {
    sumoResult.value = `❌ 仿真失败: ${e?.message || '未知错误'}`
    ElMessage.error('仿真失败，请检查 SUMO 是否安装')
  } finally { sumoRunning.value = false }
}

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
