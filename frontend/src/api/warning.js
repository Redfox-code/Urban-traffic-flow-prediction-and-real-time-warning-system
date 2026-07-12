import request from './request'
export const warningApi = {
  getList: (params) => request.get('/warning/list', { params }),
  resolve: (id) => request.put(`/warning/${id}/resolve`),
  getRules: () => request.get('/warning/rules'),
  updateRules: (data) => request.put('/warning/rules', data),
}
