<template>
  <div style="display:flex;justify-content:center;align-items:center;height:100vh;background:var(--bg-dark)">
    <el-card style="width:420px">
      <h2 style="text-align:center">注册账号</h2>
      <el-form @submit.prevent="handleRegister">
        <el-form-item>
          <el-select v-model="form.role" placeholder="选择注册角色" style="width:100%" size="large">
            <el-option label="👤 普通出行者" value="traveler">
              <span>👤 普通出行者 — 路径规划、出行提醒</span>
            </el-option>
            <el-option label="📊 数据分析员" value="analyst">
              <span>📊 数据分析员 — 模型管理、数据分析</span>
            </el-option>
            <el-option label="🛡️ 交通管理员" value="admin">
              <span>🛡️ 交通管理员 — 监控大屏、应急调度</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item><el-input v-model="form.username" placeholder="用户名" size="large" /></el-form-item>
        <el-form-item><el-input v-model="form.password" type="password" placeholder="密码" show-password size="large" /></el-form-item>
        <el-form-item><el-button type="primary" @click="handleRegister" :loading="loading" size="large" style="width:100%">注册</el-button></el-form-item>
      </el-form>
      <p style="text-align:center"><router-link to="/login">已有账号？登录</router-link></p>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api/auth'

const router = useRouter()
const loading = ref(false)
const form = ref({ username: '', password: '', role: 'traveler' })

const handleRegister = async () => {
  if (!form.value.role) return ElMessage.warning('请选择注册角色')
  loading.value = true
  try {
    await authApi.register({ username: form.value.username, password: form.value.password, role: form.value.role })
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || e?.message || '注册失败')
  } finally { loading.value = false }
}
</script>
