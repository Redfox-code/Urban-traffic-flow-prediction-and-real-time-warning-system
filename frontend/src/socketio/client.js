/** WebSocket 客户端 — Agent-Frontend-Map 负责 */
import { io } from 'socket.io-client'
import { useWarningStore } from '@/store/warning'
import { useTrafficStore } from '@/store/traffic'

const SOCKET_URL = import.meta.env.VITE_WS_URL || 'http://localhost:5000'

class SocketClient {
  constructor() {
    this.socket = null
    this.reconnectAttempts = 0
  }

  connect(token) {
    this.socket = io(SOCKET_URL, {
      auth: { token },
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 30000,
      reconnectionAttempts: 10,
      transports: ['websocket'],
    })
    this.socket.on('connect', () => { console.log('[WS] 已连接'); this.reconnectAttempts = 0 })
    this.socket.on('disconnect', (reason) => console.warn('[WS] 断开:', reason))

    // TODO D8: warning:new → AlertPopup, traffic:update → Store
    this.socket.on('warning:new', (data) => useWarningStore().addWarning(data))
    this.socket.on('traffic:update', (data) => useTrafficStore().updateRealtime(data))
  }

  subscribeSection(sectionId) { this.socket?.emit('subscribe:section', { section_id: sectionId }) }
  disconnect() { this.socket?.disconnect(); this.socket = null }
}

export const socketClient = new SocketClient()
