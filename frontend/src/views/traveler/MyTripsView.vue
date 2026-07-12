<template>
  <div class="traveler-placeholder">
    <h2>👤 我的行程</h2>
    <p>TODO: 个人行程管理 — 当前行程 + 历史行程列表 + 收藏路线</p>
    <el-card>
      <template #header>我的行程</template>
      <el-alert title="开发中 — 我的行程（需登录）" type="info" :closable="false" show-icon />
    </el-card>
  </div>
</template>
<script setup>
// FE-MAIN-04: Traveler My Trips
</script>
<style scoped>
.traveler-placeholder { padding: 20px; }
.traveler-placeholder h2 { color: var(--text-primary); margin-bottom: 16px; }
</style>
