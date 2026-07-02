import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { useUserStore } from '@/store/user'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

request.interceptors.request.use((config) => {
  const userStore = useUserStore()
  if (userStore.token) config.headers.Authorization = `Bearer ${userStore.token}`
  return config
})

request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) { useUserStore().logout(); router.push({ name: 'Login' }) }
    else if (error.response?.status >= 500) ElMessage.error('服务器错误')
    else if (error.code === 'ECONNABORTED') ElMessage.error('请求超时')
    return Promise.reject(error)
  }
)

export default request
