import { defineStore } from 'pinia'
import { getRoleFromToken } from '@/utils/jwt'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    userInfo: null,
    role: '',
    roleParsed: false,
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    isAdmin: (state) => state.role === 'admin',
    isAnalyst: (state) => state.role === 'analyst',
    isTraveler: (state) => state.role === 'traveler',
  },
  actions: {
    /** 从JWT token解析role并设置 */
    parseRoleFromToken() {
      if (this.token && !this.roleParsed) {
        const role = getRoleFromToken(this.token)
        if (role) {
          this.role = role
          this.roleParsed = true
        }
      }
    },
    /** 登录：保存token + 用户信息 + role */
    login(token, user) {
      this.token = token
      this.userInfo = user
      this.role = user?.role || getRoleFromToken(token) || ''
      this.roleParsed = true
      localStorage.setItem('token', token)
    },
    /** 退出：清除所有状态 */
    logout() {
      this.token = ''
      this.userInfo = null
      this.role = ''
      this.roleParsed = false
      localStorage.removeItem('token')
    },
  },
})
