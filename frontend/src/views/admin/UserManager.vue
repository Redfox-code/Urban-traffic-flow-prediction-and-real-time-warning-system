<template>
  <div style="color:var(--text-primary)">
    <h2>用户管理</h2>
    <el-table :data="users" v-loading="loading" style="background:var(--bg-panel)">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="role" label="角色"><template #default="{row}"><el-tag :type="row.role==='admin'?'danger':'info'">{{ row.role }}</el-tag></template></el-table-column>
      <el-table-column prop="created_at" label="创建时间" />
    </el-table>
    <el-button type="primary" @click="dialogVisible=true" style="margin-top:16px">添加用户</el-button>
    <el-dialog v-model="dialogVisible" title="添加用户">
      <el-input v-model="form.username" placeholder="用户名" style="margin-bottom:10px" />
      <el-input v-model="form.password" type="password" placeholder="密码" />
      <template #footer><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" @click="addUser">添加</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api/auth'
const users = ref([]); const loading = ref(false); const dialogVisible = ref(false)
const form = ref({ username: '', password: '' })
onMounted(async () => { /* TODO: 用户列表API */ })
const addUser = async () => { try { await authApi.register({...form.value, role:'analyst'}); ElMessage.success('添加成功'); dialogVisible.value = false } catch {} }
</script>
