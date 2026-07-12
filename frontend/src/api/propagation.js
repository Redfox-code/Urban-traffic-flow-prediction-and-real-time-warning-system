import request from './request'

export const propagationApi = {
  analyze: (data) => request.post('/propagation/analyze', data),
  getActive: () => request.get('/propagation/active'),
  getHistory: (params) => request.get('/propagation/history', { params }),
  getHistoryDetail: (eventId) => request.get(`/propagation/history/${eventId}`),
}
