import request from './request'
export const authApi = {
  login: (data) => request.post('/auth/login', data),
  register: (data) => request.post('/auth/register', data),
  refresh: () => request.post('/auth/refresh'),
}
