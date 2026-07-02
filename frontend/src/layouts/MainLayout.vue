<template>
  <el-container style="height: 100vh">
    <el-aside width="220px" style="background: var(--bg-panel); color: var(--text-primary)">
      <el-menu :default-active="route.path" router background-color="transparent" text-color="#8899aa" active-text-color="#00d4ff">
        <el-menu-item index="/dashboard">🏠 系统首页</el-menu-item>
        <el-menu-item index="/traffic">📡 实时路况</el-menu-item>
        <el-menu-item index="/prediction">📈 流量预测</el-menu-item>
        <el-menu-item index="/warnings">⚠️ 预警管理</el-menu-item>
        <el-menu-item index="/route-plan">🗺️ 路径规划</el-menu-item>
        <el-menu-item v-if="userStore.isAdmin" index="/admin/users">👤 用户管理</el-menu-item>
        <el-menu-item v-if="userStore.isAdmin" index="/admin/logs">📋 系统日志</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="background:var(--bg-panel); color:var(--text-primary); display:flex; align-items:center; justify-content:space-between">
        <span style="font-size:18px;font-weight:bold">🚦 智能交通管理平台</span>
        <span>{{ userStore.userInfo?.username }} | <a @click="logout" style="cursor:pointer;color:#00d4ff">退出</a></span>
      </el-header>
      <el-main style="background:var(--bg-dark)"><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
const route = useRoute(); const router = useRouter(); const userStore = useUserStore()
const logout = () => { userStore.logout(); router.push('/login') }
</script>
