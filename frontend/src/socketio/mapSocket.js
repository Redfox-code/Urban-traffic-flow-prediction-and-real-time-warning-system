/**
 * mapSocket.js — WebSocket地图实时更新客户端
 *
 * 职责：
 * - /ws/admin 路况更新监听 → 触发地图图层刷新
 * - 预警新消息 → 路段红色脉冲闪烁
 * - 重连指数退避 + 断连提示条
 *
 * 使用：import { mapSocket } from '@/socketio/mapSocket'
 *       mapSocket.connect(token)
 *       mapSocket.onTrafficUpdate((data) => { ... })
 *       mapSocket.onWarning((data) => { ... })
 *
 * Agent-Frontend-Map 维护
 */

import { io } from 'socket.io-client'

const SOCKET_URL = import.meta.env.VITE_WS_URL || 'http://localhost:5000'

class MapSocket {
  constructor() {
    this.socket = null
    this.connected = false
    this.reconnectAttempts = 0
    this.maxReconnectDelay = 30000
    this.baseReconnectDelay = 1000

    // 回调列表
    this._trafficCallbacks = []
    this._warningCallbacks = []
    this._connectionCallbacks = []
    this._disconnectCallbacks = []

    // 断连提示条DOM
    this._disconnectBanner = null
  }

  /**
   * 建立连接
   * @param {string} token - JWT令牌
   * @param {string} namespace - Socket.IO命名空间（默认/admin）
   */
  connect(token, namespace = '/admin') {
    if (this.socket?.connected) return

    this.socket = io(SOCKET_URL + namespace, {
      auth: { token },
      reconnection: true,
      reconnectionDelay: this.baseReconnectDelay,
      reconnectionDelayMax: this.maxReconnectDelay,
      reconnectionAttempts: Infinity,
      transports: ['websocket'],
      timeout: 10000,
    })

    this.socket.on('connect', () => {
      console.log('[MapSocket] 已连接')
      this.connected = true
      this.reconnectAttempts = 0
      this._hideDisconnectBanner()
      this._connectionCallbacks.forEach(cb => cb())
    })

    this.socket.on('disconnect', (reason) => {
      console.warn('[MapSocket] 断开:', reason)
      this.connected = false
      this._showDisconnectBanner()
      this._disconnectCallbacks.forEach(cb => cb(reason))
    })

    this.socket.on('connect_error', (err) => {
      console.error('[MapSocket] 连接错误:', err.message)
      this.reconnectAttempts++
      this._showDisconnectBanner()
    })

    this.socket.on('reconnect_attempt', (attempt) => {
      this.reconnectAttempts = attempt
      const delay = Math.min(
        this.baseReconnectDelay * Math.pow(2, attempt),
        this.maxReconnectDelay
      )
      console.log(`[MapSocket] 重连第 ${attempt} 次，延迟 ${delay}ms`)
    })

    // === 业务事件 ===

    // 路况更新（单路段）
    this.socket.on('traffic:update', (data) => {
      this._trafficCallbacks.forEach(cb => cb(data))
    })

    // 批量路况更新
    this.socket.on('traffic:batch', (dataArray) => {
      if (Array.isArray(dataArray)) {
        dataArray.forEach(data => {
          this._trafficCallbacks.forEach(cb => cb(data))
        })
      }
    })

    // 预警新消息 → 触发路段红色脉冲闪烁
    this.socket.on('warning:new', (data) => {
      this._warningCallbacks.forEach(cb => cb(data))
    })

    // 预警状态变更
    this.socket.on('warning:update', (data) => {
      console.log('[MapSocket] 预警更新:', data)
    })

    // 预警解除
    this.socket.on('warning:resolve', (data) => {
      console.log('[MapSocket] 预警解除:', data)
    })
  }

  /**
   * 注册路况更新回调
   * @param {Function} cb - (data) => void
   * @returns {Function} 取消注册函数
   */
  onTrafficUpdate(cb) {
    this._trafficCallbacks.push(cb)
    return () => {
      this._trafficCallbacks = this._trafficCallbacks.filter(c => c !== cb)
    }
  }

  /**
   * 注册预警回调
   * @param {Function} cb - (data) => void
   * @returns {Function} 取消注册函数
   */
  onWarning(cb) {
    this._warningCallbacks.push(cb)
    return () => {
      this._warningCallbacks = this._warningCallbacks.filter(c => c !== cb)
    }
  }

  /**
   * 注册连接成功回调
   */
  onConnect(cb) {
    this._connectionCallbacks.push(cb)
    return () => {
      this._connectionCallbacks = this._connectionCallbacks.filter(c => c !== cb)
    }
  }

  /**
   * 注册断开回调
   */
  onDisconnect(cb) {
    this._disconnectCallbacks.push(cb)
    return () => {
      this._disconnectCallbacks = this._disconnectCallbacks.filter(c => c !== cb)
    }
  }

  /**
   * 订阅路段
   * @param {number} sectionId - 路段ID（0=全部）
   */
  subscribeSection(sectionId) {
    this.socket?.emit('subscribe:section', { section_id: sectionId })
  }

  /**
   * 取消订阅路段
   */
  unsubscribeSection(sectionId) {
    this.socket?.emit('unsubscribe:section', { section_id: sectionId })
  }

  /**
   * 断开连接
   */
  disconnect() {
    this._hideDisconnectBanner()
    this.socket?.disconnect()
    this.socket = null
    this.connected = false
  }

  // ===== 私有方法 =====

  /** 显示断连提示条 */
  _showDisconnectBanner() {
    if (this._disconnectBanner) return
    const banner = document.createElement('div')
    banner.className = 'mapsocket-banner'
    banner.innerHTML = `
      <span class="mapsocket-banner-icon">🔌</span>
      <span class="mapsocket-banner-text">与服务器的连接已断开，正在重连...</span>
      <span class="mapsocket-banner-attempt">第 ${this.reconnectAttempts} 次</span>
    `
    document.body.appendChild(banner)
    this._disconnectBanner = banner

    // 添加动画
    requestAnimationFrame(() => banner.classList.add('mapsocket-banner-show'))
  }

  /** 隐藏断连提示条 */
  _hideDisconnectBanner() {
    if (this._disconnectBanner) {
      this._disconnectBanner.classList.remove('mapsocket-banner-show')
      setTimeout(() => {
        this._disconnectBanner?.remove()
        this._disconnectBanner = null
      }, 300)
    }
  }
}

// 单例导出
export const mapSocket = new MapSocket()

// 注入全局CSS（断连提示条样式）
const styleId = 'mapsocket-styles'
if (!document.getElementById(styleId)) {
  const style = document.createElement('style')
  style.id = styleId
  style.textContent = `
    .mapsocket-banner {
      position: fixed;
      top: -60px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 99999;
      background: rgba(245,34,45,.95);
      color: #fff;
      padding: 10px 20px;
      border-radius: 0 0 12px 12px;
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 13px;
      box-shadow: 0 4px 20px rgba(245,34,45,.4);
      transition: top .3s ease;
      white-space: nowrap;
      backdrop-filter: blur(8px);
    }
    .mapsocket-banner-show {
      top: 0 !important;
    }
    .mapsocket-banner-icon { font-size: 16px; }
    .mapsocket-banner-text { font-weight: 500; }
    .mapsocket-banner-attempt {
      font-size: 11px;
      opacity: .7;
      margin-left: 4px;
    }

    @media (max-width: 768px) {
      .mapsocket-banner {
        font-size: 11px;
        padding: 8px 14px;
        width: 90%;
        white-space: normal;
      }
    }
  `
  document.head.appendChild(style)
}
