<template>
  <div class="admin-placeholder">
    <h2>📊 实时监控</h2>
    <p>TODO: 集成 TrafficMonitor 核心数据面板 — 路段列表 + 路况 Badge + 地图组件</p>
    <el-card>
      <template #header>实时路况概览</template>
      <el-alert title="开发中 — 管理员监控面板" type="info" :closable="false" show-icon />
    </el-card>
  </div>
</template>
<script setup>
// FE-MAIN-02: Admin Dashboard
</script>
<style scoped>
.admin-placeholder { padding: 20px; }
.admin-placeholder h2 { color: var(--text-primary); margin-bottom: 16px; }
</style>
