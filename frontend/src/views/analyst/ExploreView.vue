<template>
  <div class="analyst-placeholder">
    <h2>📊 数据探索</h2>
    <p>TODO: 历史数据多维探索 — 时间/路段/天气筛选 + ECharts 趋势图 + 数据导出</p>
    <el-card>
      <template #header>数据探索工具</template>
      <el-alert title="开发中 — 数据探索面板" type="info" :closable="false" show-icon />
    </el-card>
  </div>
</template>
<script setup>
// FE-MAIN-03: Analyst Explore
</script>
<style scoped>
.analyst-placeholder { padding: 20px; }
.analyst-placeholder h2 { color: var(--text-primary); margin-bottom: 16px; }
</style>
