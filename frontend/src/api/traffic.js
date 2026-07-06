import request from './request'
export const trafficApi = {
  getCurrent: (sectionId) => {
    const params = sectionId != null ? { section_id: sectionId } : {}
    return request.get('/traffic/current', { params })
  },
  getHistory: (params) => request.get('/traffic/history', { params }),
}
