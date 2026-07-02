<template>
  <div style="color:var(--text-primary)">
    <h2>预警管理</h2>
    <el-radio-group v-model="filter" style="margin-bottom:16px" @change="fetchWarnings">
      <el-radio-button value="">全部</el-radio-button>
      <el-radio-button value="active">未解除</el-radio-button>
      <el-radio-button value="CRITICAL">严重</el-radio-button>
    </el-radio-group>
    <el-table :data="warnings" style="background:var(--bg-panel)" v-loading="loading" empty-text="暂无预警">
      <el-table-column prop="section_name" label="路段" />
      <el-table-column prop="level" label="等级"><template #default="{row}"><el-tag :type="row.level==='CRITICAL'?'danger':'warning'">{{ row.level }}</el-tag></template></el-table-column>
      <el-table-column prop="message" label="描述" />
      <el-table-column prop="created_at" label="时间" />
      <el-table-column label="操作"><template #default="{row}"><el-button v-if="!row.is_resolved" size="small" type="success" @click="resolveWarning(row.id)">解除</el-button></template></el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { warningApi } from '@/api/warning'
const warnings = ref([]); const filter = ref(''); const loading = ref(false)
const fetchWarnings = async () => {
  loading.value = true
  const params = {}
  if (filter.value === 'active') params.is_resolved = 'false'
  else if (filter.value === 'CRITICAL') params.level = 'CRITICAL'
  try { const res = await warningApi.getList(params); warnings.value = res.data?.items || res?.items || [] }
  finally { loading.value = false }
}
const resolveWarning = async (id) => { await warningApi.resolve(id); fetchWarnings() }
onMounted(fetchWarnings)
</script>
