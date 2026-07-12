import request from './request'

/**
 * 应急调度 API 模块
 * 路径: /api/v1/emergency/*
 */
export const emergencyApi = {
  /** 计算应急最优路径 + 绿波带建议 */
  plan: (data) => request.post('/emergency/plan', data),

  /** 获取调度记录列表（分页） */
  getRecords: (params) => request.get('/emergency/records', { params }),

  /** 创建调度记录 */
  createRecord: (data) => request.post('/emergency/records', data),

  /** 获取单条调度记录详情 */
  getRecord: (id) => request.get(`/emergency/records/${id}`),

  /** 更新调度状态 (active/completed/cancelled) */
  updateStatus: (id, status) => request.put(`/emergency/records/${id}/status`, { status }),
}
