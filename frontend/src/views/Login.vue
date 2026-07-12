<template>
  <div style="display:flex;justify-content:center;align-items:center;height:100vh;background:var(--bg-dark)">
    <el-card style="width:420px">
      <h2 style="text-align:center">🚦 智能交通系统</h2>
      <el-form @submit.prevent="handleLogin">
        <el-form-item>
          <el-select v-model="form.role" placeholder="选择登录角色" style="width:100%" size="large">
            <el-option label="👤 普通出行者" value="traveler" />
            <el-option label="📊 数据分析员" value="analyst" />
            <el-option label="🛡️ 交通管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item><el-input v-model="form.username" placeholder="用户名" size="large" /></el-form-item>
        <el-form-item><el-input v-model="form.password" type="password" placeholder="密码" show-password size="large" /></el-form-item>
        <el-form-item><el-button type="primary" @click="handleLogin" :loading="loading" size="large" style="width:100%">登录</el-button></el-form-item>
      </el-form>
      <p style="text-align:center"><router-link to="/register">没有账号？注册</router-link></p>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api/auth'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const form = ref({ username: '', password: '', role: 'analyst' })

const roleHomeMap = {
  admin: '/admin/dashboard',
  analyst: '/analyst/models',
  traveler: '/traveler/route-plan',
}

const handleLogin = async () => {
  if (!form.value.role) return ElMessage.warning('请选择登录角色')
  loading.value = true
  try {
    const res = await authApi.login(form.value)
    userStore.login(res.data.token, res.data.user)
    ElMessage.success('登录成功')
    router.push(roleHomeMap[form.value.role] || '/analyst/models')
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || e?.message || '登录失败')
  } finally { loading.value = false }
}
</script>
