<template>
  <div class="traveler-placeholder">
    <h2>🏠 路径规划</h2>
    <p>TODO: 起终点选择 + 路径推荐 + 路线时间线 + 地图可视化（集成高德地图）</p>
    <el-card>
      <template #header>智能路径规划</template>
      <el-alert title="出行者路径规划（免登录可用）" type="success" :closable="false" show-icon />
    </el-card>
  </div>
</template>
<script setup>
// FE-MAIN-04: Traveler Route Plan
</script>
<style scoped>
.traveler-placeholder { padding: 20px; }
.traveler-placeholder h2 { color: var(--text-primary); margin-bottom: 16px; }
</style>
