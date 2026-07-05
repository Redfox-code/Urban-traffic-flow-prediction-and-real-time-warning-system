import { defineStore } from 'pinia'
import request from '@/api/request'

export const useSimulationStore = defineStore('simulation', {
  state: () => ({
    realtimeRunning: false,
    realtimePaused: false,
    batchRunning: false,
    progress: 0,
    message: '',
  }),

  actions: {
    async checkStatus() {
      try {
        const res = await request.get('/sumo/status')
        const d = res.data || res || {}
        this.realtimeRunning = d.realtime_running || false
        this.batchRunning = d.batch_running || false
        this.progress = d.progress || 0
      } catch {}
    },

    async startRealtime() {
      this.message = ''
      try { await request.post('/sumo/run_realtime', null, { timeout: 10000 }); this.realtimeRunning = true; this.message = '✅ 已启动' }
      catch (e) { this.message = '❌ ' + (e?.message || '失败') }
    },

    async stopRealtime() {
      try { await request.post('/sumo/stop'); this.realtimeRunning = false; this.realtimePaused = false; this.message = '⏹ 已停止' }
      catch { this.realtimeRunning = false }
    },

    async pauseRealtime() {
      try { await request.post('/sumo/pause'); this.realtimePaused = true; this.message = '⏸ 已暂停' }
      catch {}
    },

    async resumeRealtime() {
      try { await request.post('/sumo/resume'); this.realtimePaused = false; this.message = '▶ 已继续' }
      catch {}
    },

    async stopBatch() {
      try { await request.post('/sumo/batch/stop'); this.batchRunning = false; this.message = '⏹ 已停止' }
      catch { this.batchRunning = false }
    },

    async runBatch() {
      this.batchRunning = true; this.message = ''
      try {
        const res = await request.post('/sumo/run', null, { timeout: 180000 })
        const d = res.data || res
        this.message = `✅ 完成 (${d.records_imported || 0}条记录)`
      } catch (e) {
        this.message = '❌ ' + (e?.message || '失败')
      } finally { this.batchRunning = false }
    },
  },
})
