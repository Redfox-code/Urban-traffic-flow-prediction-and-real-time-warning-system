import request from './request'

export const carbonApi = {
  getCurrent: () => request.get('/carbon/current'),
  getTrend: (period = 'day') => request.get('/carbon/trend', { params: { period } }),
  getSectionTop: (limit = 10) => request.get('/carbon/sections/top', { params: { limit } }),
  estimate: (data) => request.post('/carbon/estimate', data),
  getComparison: () => request.get('/carbon/comparison'),
}
