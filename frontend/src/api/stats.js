import request from './request'
export const statsApi = { getDashboard: () => request.get('/stats/dashboard') }
