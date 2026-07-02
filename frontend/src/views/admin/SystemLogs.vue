<template>
  <div style="color:var(--text-primary)">
    <h2>系统日志</h2>
    <el-table :data="logs" style="background:var(--bg-panel)">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="action" label="操作" />
      <el-table-column prop="created_at" label="时间" />
    </el-table>
  </div>
</template>
<script setup>
import { ref } from 'vue'
const logs = ref([])
// TODO: 系统日志API
</script>
