<template>
  <div class="admin-placeholder">
    <h2>📈 统计报表</h2>
    <p>TODO: ECharts 统计报表 — 流量趋势 + 拥堵时段 + 预警统计 + 导出 PDF</p>
    <el-card>
      <template #header>数据报表</template>
      <el-alert title="开发中 — 报表面板" type="info" :closable="false" show-icon />
    </el-card>
  </div>
</template>
<script setup>
// FE-MAIN-02: Admin Reports
</script>
<style scoped>
.admin-placeholder { padding: 20px; }
.admin-placeholder h2 { color: var(--text-primary); margin-bottom: 16px; }
</style>
