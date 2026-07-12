import request from './request'

/**
 * 信号优化 API 模块
 * 路径: /api/v1/signal/*
 */
export const signalApi = {
  /** 获取路口列表（按优化潜力降序） */
  getIntersections: () => request.get('/signal/intersections'),

  /** 计算单个路口的Webster最优配时 */
  calculate: (data) => request.post('/signal/calculate', data),

  /** 应用建议配时方案 */
  apply: (optimizationId) => request.post('/signal/apply', { optimization_id: optimizationId }),

  /** 获取优化历史记录 */
  getHistory: () => request.get('/signal/history'),

  /** 获取信号优化效果统计 */
  getStats: () => request.get('/signal/stats'),
}
