<template>
  <div class="admin-placeholder">
    <h2>🚨 预警管理</h2>
    <p>TODO: 集成 WarningManager 核心功能 — 预警列表 + 等级筛选 + 解除操作</p>
    <el-card>
      <template #header>预警规则引擎</template>
      <el-alert title="开发中 — 管理员预警管理面板" type="warning" :closable="false" show-icon />
    </el-card>
  </div>
</template>
<script setup>
// FE-MAIN-02: Admin Warnings
</script>
<style scoped>
.admin-placeholder { padding: 20px; }
.admin-placeholder h2 { color: var(--text-primary); margin-bottom: 16px; }
</style>
