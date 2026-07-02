import request from './request'
export const warningApi = {
  getList: (params) => request.get('/warning/list', { params }),
  resolve: (id) => request.put(`/warning/${id}/resolve`),
}
