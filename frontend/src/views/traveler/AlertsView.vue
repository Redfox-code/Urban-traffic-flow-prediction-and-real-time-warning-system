<template>
  <div class="traveler-placeholder">
    <h2>🔔 出行提醒</h2>
    <p>TODO: 实时出行提醒推送 — 拥堵预警 + 事故通知 + 限行提醒</p>
    <el-card>
      <template #header>出行提醒</template>
      <el-alert title="开发中 — 出行提醒（需登录）" type="warning" :closable="false" show-icon />
    </el-card>
  </div>
</template>
<script setup>
// FE-MAIN-04: Traveler Alerts
</script>
<style scoped>
.traveler-placeholder { padding: 20px; }
.traveler-placeholder h2 { color: var(--text-primary); margin-bottom: 16px; }
</style>
