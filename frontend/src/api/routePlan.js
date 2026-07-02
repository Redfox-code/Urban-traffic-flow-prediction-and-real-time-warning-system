import request from './request'
export const routeApi = { plan: (data) => request.post('/route/plan', data) }
