import { defineStore } from 'pinia'

export const useWarningStore = defineStore('warning', {
  state: () => ({
    warnings: [],
    unreadCount: 0,
    filter: { level: '', is_resolved: false },
    isLoading: false,
  }),
  getters: {
    activeWarnings: (state) => state.warnings.filter(w => !w.is_resolved),
  },
  actions: {
    addWarning(warning) { this.warnings.unshift(warning); if (!warning.is_resolved) this.unreadCount++ },
  },
})
