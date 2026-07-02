<template>
  <div style="color:var(--text-primary)">
    <h2>路径规划</h2>
    <el-row :gutter="20">
      <el-col :span="8"><el-select v-model="origin" placeholder="起点路段"><el-option v-for="s in sections" :key="s.id" :label="s.name" :value="s.id" /></el-select></el-col>
      <el-col :span="8"><el-select v-model="dest" placeholder="终点路段"><el-option v-for="s in sections" :key="s.id" :label="s.name" :value="s.id" /></el-select></el-col>
      <el-col :span="8"><el-button type="primary" @click="planRoute" :loading="loading">规划路径</el-button></el-col>
    </el-row>
    <el-card v-if="result" style="background:var(--bg-panel);margin-top:16px">
      <p>总距离: <b>{{ result.total_distance }} km</b> | 预估时间: <b>{{ result.estimated_time }} min</b></p>
      <el-timeline><el-timeline-item v-for="p in result.path" :key="p.section_id" :timestamp="p.name">{{ p.length }} km</el-timeline-item></el-timeline>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { routeApi } from '@/api/routePlan'
import { sectionsApi } from '@/api/sections'
const sections = ref([]); const origin = ref(null); const dest = ref(null)
const loading = ref(false); const result = ref(null)
onMounted(async () => { try { const res = await sectionsApi.getList(); sections.value = res.data?.items || [] } catch {} })
const planRoute = async () => {
  if (!origin.value || !dest.value) return; loading.value = true
  try { const res = await routeApi.plan({ origin_section_id: origin.value, dest_section_id: dest.value }); result.value = res.data }
  finally { loading.value = false }
}
</script>
