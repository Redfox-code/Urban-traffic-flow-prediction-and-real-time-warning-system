import { defineStore } from 'pinia'

export const useWarningStore = defineStore('warning', {
  state: () => ({
    warnings: [],
    unreadCount: 0,
    filter: { level: '', is_resolved: false },
    isLoading: false,
    flashSectionId: null,       // 预警闪烁路段ID（地图脉冲）
  }),
  getters: {
    activeWarnings: (state) => state.warnings.filter(w => !w.is_resolved),
  },
  actions: {
    addWarning(warning) {
      this.warnings.unshift(warning)
      if (!warning.is_resolved) {
        this.unreadCount++
        // 触发路段闪烁
        this.flashSectionId = warning.section_id
        setTimeout(() => { this.flashSectionId = null }, 3000)
      }
    },
    dismissFlash() { this.flashSectionId = null },
  },
})
