import request from './request'
export const sectionsApi = { getList: (params) => request.get('/sections', { params }) }
