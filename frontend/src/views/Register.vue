<template>
  <div style="display:flex;justify-content:center;align-items:center;height:100vh;background:var(--bg-dark)">
    <el-card style="width:400px">
      <h2 style="text-align:center">注册账号</h2>
      <el-form>
        <el-form-item><el-input v-model="form.username" placeholder="用户名" /></el-form-item>
        <el-form-item><el-input v-model="form.password" type="password" placeholder="密码" show-password /></el-form-item>
        <el-form-item><el-button type="primary" @click="handleRegister" :loading="loading" style="width:100%">注册</el-button></el-form-item>
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
const form = ref({ username: '', password: '' })
const handleRegister = async () => {
  loading.value = true
  try { await authApi.register({ ...form.value, role: 'analyst' }); ElMessage.success('注册成功'); router.push('/login') }
  catch (e) { ElMessage.error(e?.message || '注册失败') }
  finally { loading.value = false }
}
</script>
