import request from './request'

export const scenarioApi = {
  list: (params) => request.get('/scenario/scenarios', { params }),
  create: (data) => request.post('/scenario/create', data),
  get: (id) => request.get(`/scenario/${id}`),
  run: (id) => request.post(`/scenario/${id}/run`),
  getResult: (id) => request.get(`/scenario/${id}/result`),
  delete: (id) => request.delete(`/scenario/${id}`),
}
