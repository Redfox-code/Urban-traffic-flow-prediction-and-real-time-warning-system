<template>
  <div class="traveler-placeholder">
    <h2>⚙️ 账户设置</h2>
    <p>TODO: 个人资料编辑 + 密码修改 + 偏好设置 + 常用路线管理</p>
    <el-card>
      <template #header>账户设置</template>
      <el-alert title="开发中 — 账户设置（需登录）" type="info" :closable="false" show-icon />
    </el-card>
  </div>
</template>
<script setup>
// FE-MAIN-04: Traveler Account
</script>
<style scoped>
.traveler-placeholder { padding: 20px; }
.traveler-placeholder h2 { color: var(--text-primary); margin-bottom: 16px; }
</style>
