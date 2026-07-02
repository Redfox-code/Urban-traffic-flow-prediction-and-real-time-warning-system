<template>
  <div style="color:var(--text-primary)">
    <h2>流量预测看板</h2>
    <el-row :gutter="20" style="margin-bottom:16px">
      <el-col :span="6"><el-select v-model="sectionId" placeholder="选择路段" style="width:100%" @change="fetchPrediction"><el-option v-for="s in sections" :key="s.id" :label="s.name" :value="s.id" /></el-select></el-col>
      <el-col :span="4"><el-select v-model="model" style="width:100%"><el-option label="随机森林(RF)" value="RF" /><el-option label="KNN回归" value="KNN" /></el-select></el-col>
      <el-col :span="4"><el-select v-model="horizon" style="width:100%"><el-option label="15分钟" :value="15" /><el-option label="30分钟" :value="30" /><el-option label="5分钟" :value="5" /></el-select></el-col>
      <el-col :span="4"><el-button type="primary" @click="fetchPrediction" :loading="loading" style="width:100%">开始预测</el-button></el-col>
    </el-row>

    <el-alert v-if="errorMsg" :title="errorMsg" type="warning" show-icon closable @close="errorMsg=''" style="margin-bottom:16px" />

    <el-card v-if="result" style="background:var(--bg-panel);margin-bottom:16px">
      <div style="display:flex;gap:24px;flex-wrap:wrap">
        <div style="flex:1;min-width:180px">
          <div style="font-size:13px;color:var(--text-secondary)">预测流量</div>
          <div style="font-size:36px;font-weight:bold;color:var(--accent-blue)">{{ result.predicted_flow }} <span style="font-size:14px">veh/h</span></div>
        </div>
        <div style="flex:1;min-width:180px">
          <div style="font-size:13px;color:var(--text-secondary)">置信区间</div>
          <div style="font-size:20px;color:var(--text-primary)">{{ result.confidence_interval?.lower }} ~ {{ result.confidence_interval?.upper }}</div>
        </div>
        <div style="flex:1;min-width:120px">
          <div style="font-size:13px;color:var(--text-secondary)">模型</div>
          <div style="font-size:20px;color:var(--text-primary)">{{ result.model }} <el-tag v-if="!result.using_trained_model" size="small" type="warning">模拟</el-tag></div>
        </div>
      </div>
    </el-card>

    <el-card v-if="result?.predictions" style="background:var(--bg-panel)">
      <template #header><span style="font-weight:bold">📈 预测序列 ({{ result.horizon }}分钟)</span></template>
      <div style="display:flex;gap:12px;flex-wrap:wrap">
        <div v-for="p in result.predictions" :key="p.timestamp" class="pred-point">
          <div style="font-size:12px;color:var(--text-secondary)">{{ p.timestamp.slice(11,16) }}</div>
          <div style="font-size:20px;font-weight:bold;color:var(--accent-blue)">{{ p.predicted_flow }}</div>
          <div style="font-size:11px;color:var(--text-secondary)">veh/h</div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { predictionApi } from '@/api/prediction'
import { sectionsApi } from '@/api/sections'
const sections = ref([]); const sectionId = ref(null); const model = ref('RF')
const horizon = ref(15); const loading = ref(false); const result = ref(null)
const errorMsg = ref('')
onMounted(async () => {
  try { const res = await sectionsApi.getList(); sections.value = res.data?.items || res?.items || [] } catch {}
})
const fetchPrediction = async () => {
  if (!sectionId.value) { errorMsg.value = '请先选择路段'; return }
  errorMsg.value = ''; loading.value = true; result.value = null
  try { const res = await predictionApi.getForecast(sectionId.value, horizon.value, model.value); result.value = res.data || res }
  catch (e) { errorMsg.value = e?.message || '预测请求失败，请确认后端已启动' }
  finally { loading.value = false }
}
</script>

<style scoped>
.pred-point {
  background: rgba(0,212,255,.06); border-radius: 10px; padding: 12px 16px;
  text-align: center; min-width: 80px;
  border: 1px solid rgba(0,212,255,.12);
}
</style>
