<template>
  <div class="account-view">
    <h2>⚙️ 账户设置</h2>
    <el-card shadow="never" style="background:var(--bg-panel);margin-bottom:16px">
      <template #header><span style="font-weight:bold">👤 基本信息</span></template>
      <div v-if="userStore.isLoggedIn" style="display:flex;flex-direction:column;gap:12px">
        <div><span style="color:var(--text-secondary)">用户名：</span><strong>{{ userStore.userInfo?.username || '-' }}</strong></div>
        <div><span style="color:var(--text-secondary)">角色：</span><el-tag size="small">{{ userStore.userInfo?.role || 'traveler' }}</el-tag></div>
        <div><span style="color:var(--text-secondary)">注册时间：</span>{{ userStore.userInfo?.created_at?.slice(0,10) || '-' }}</div>
      </div>
      <el-empty v-else description="请先登录" :image-size="80" />
    </el-card>

    <el-card shadow="never" style="background:var(--bg-panel);margin-bottom:16px">
      <template #header><span style="font-weight:bold">🚗 出行偏好</span></template>
      <el-form label-width="100px" size="default">
        <el-form-item label="默认出发时间"><el-time-select v-model="prefs.defaultTime" start="06:00" step="00:30" end="23:00" /></el-form-item>
        <el-form-item label="通勤提醒"><el-switch v-model="prefs.commuteAlert" /></el-form-item>
        <el-form-item label="提前提醒">
          <el-select v-model="prefs.alertBefore" size="small" style="width:120px">
            <el-option :value="15" label="15分钟" /><el-option :value="30" label="30分钟" /><el-option :value="60" label="60分钟" />
          </el-select>
        </el-form-item>
        <el-form-item><el-button type="primary" @click="savePrefs">保存偏好</el-button></el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, onMounted } from 'vue'
import { useUserStore } from '@/store/user'
import { travelerApi } from '@/api/traveler'
import { ElMessage } from 'element-plus'
const userStore = useUserStore()
const prefs = reactive({ defaultTime: '08:00', commuteAlert: true, alertBefore: 30 })

onMounted(async () => {
  if (!userStore.isLoggedIn) return
  try {
    const res = await travelerApi.getPreferences()
    const p = res.data?.preferences || res?.preferences
    if (p) Object.assign(prefs, p)
  } catch {}
})

const savePrefs = async () => {
  try {
    await travelerApi.updatePreferences({ preferences: { ...prefs } })
    ElMessage.success('偏好已保存')
  } catch { ElMessage.error('保存失败') }
}
</script>

<style scoped>
.account-view { padding:20px; max-width:600px }
.account-view h2 { color:var(--text-primary); margin-bottom:20px }
</style>
