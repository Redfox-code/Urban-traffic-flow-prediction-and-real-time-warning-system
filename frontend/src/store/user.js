import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    userInfo: null,
    role: '',
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    isAdmin: (state) => state.role === 'admin',
  },
  actions: {
    login(token, user) { this.token = token; this.userInfo = user; this.role = user.role; localStorage.setItem('token', token) },
    logout() { this.token = ''; this.userInfo = null; this.role = ''; localStorage.removeItem('token') },
  },
})
