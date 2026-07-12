import request from './request'

/**
 * 出行者 API 模块
 * 路径: /api/v1/traveler/*
 */
export const travelerApi = {
  // ===== 画像 =====
  /** 获取出行画像（常用路线列表） */
  getProfile: () => request.get('/traveler/profile'),
  /** 保存常用路线 */
  saveRoute: (data) => request.post('/traveler/profile/route', data),
  /** 删除常用路线 */
  deleteRoute: (id) => request.delete(`/traveler/profile/route/${id}`),
  /** 更新路线标签 */
  updateRouteLabel: (id, label) => request.put(`/traveler/profile/route/${id}/label`, { label }),

  // ===== 提醒 =====
  /** 获取提醒列表（分页） */
  getAlerts: (params) => request.get('/traveler/alerts', { params }),
  /** 标记提醒已读 */
  markRead: (id) => request.put(`/traveler/alerts/${id}/read`),
  /** 批量标记已读 */
  batchRead: (ids) => request.post('/traveler/alerts/batch-read', { alert_ids: ids }),
  /** 更新提醒设置 */
  updateAlertSettings: (data) => request.put('/traveler/alerts/settings', data),

  // ===== 历史 =====
  /** 获取查询历史（分页） */
  getHistory: (params) => request.get('/traveler/history', { params }),
  /** 保存历史记录 */
  saveHistory: (data) => request.post('/traveler/history', data),
  /** 删除单条历史 */
  deleteHistory: (id) => request.delete(`/traveler/history/${id}`),
  /** 清空全部历史 */
  clearHistory: () => request.delete('/traveler/history'),
}
