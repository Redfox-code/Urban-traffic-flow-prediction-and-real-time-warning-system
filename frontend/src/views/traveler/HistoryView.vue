<template>
  <div class="traveler-placeholder">
    <h2>📋 历史记录</h2>
    <p>TODO: 出行历史记录 — 路线 + 时间 + 路况 + 统计</p>
    <el-card>
      <template #header>历史记录</template>
      <el-alert title="开发中 — 历史记录（需登录）" type="info" :closable="false" show-icon />
    </el-card>
  </div>
</template>
<script setup>
// FE-MAIN-04: Traveler History
</script>
<style scoped>
.traveler-placeholder { padding: 20px; }
.traveler-placeholder h2 { color: var(--text-primary); margin-bottom: 16px; }
</style>
