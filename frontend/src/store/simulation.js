/** 仿真全局状态 — 跨页面共享，切换页面不丢失 */
import { defineStore } from 'pinia'
import request from '@/api/request'

export const useSimulationStore = defineStore('simulation', {
  state: () => ({
    realtimeRunning: false,   // 实时仿真是否在运行
    batchRunning: false,      // 离线仿真是否在运行
    message: '',              // 提示消息
  }),

  actions: {
    async checkStatus() {
      try {
        const res = await request.get('/sumo/status')
        this.realtimeRunning = res.data?.running || res?.running || false
      } catch {}
    },

    async startRealtime() {
      this.message = ''
      try {
        await request.post('/sumo/run_realtime', null, { timeout: 10000 })
        this.realtimeRunning = true
        this.message = '✅ 实时仿真已启动'
      } catch (e) {
        this.message = '❌ 启动失败: ' + (e?.message || '')
      }
    },

    async stopRealtime() {
      try {
        await request.post('/sumo/stop')
        this.realtimeRunning = false
        this.message = '⏹ 已停止'
      } catch {
        this.realtimeRunning = false
      }
    },

    async runBatch() {
      this.batchRunning = true
      this.message = ''
      try {
        const res = await request.post('/sumo/run', null, { timeout: 180000 })
        const d = res.data || res
        this.message = `✅ 完成 (${d.records_imported || 0}条记录)`
      } catch (e) {
        this.message = '❌ ' + (e?.message || '失败')
      } finally {
        this.batchRunning = false
      }
    },
  },
})
