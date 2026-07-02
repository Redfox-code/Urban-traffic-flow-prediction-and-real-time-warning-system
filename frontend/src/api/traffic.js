import request from './request'
export const trafficApi = {
  getCurrent: (sectionId) => request.get('/traffic/current', { params: { section_id: sectionId } }),
  getHistory: (params) => request.get('/traffic/history', { params }),
}
