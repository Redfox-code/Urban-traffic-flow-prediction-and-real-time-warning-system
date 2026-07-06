import request from './request'
export const predictionApi = {
  getForecast: (sectionId, horizon = 15, model = 'RF') => request.get('/predict/forecast', { params: { section_id: sectionId, horizon, model } }),
  getAccuracy: (sectionId) => request.get('/predict/accuracy', { params: { section_id: sectionId } }),
  getAnalysis: (sectionId, horizon = 15) => request.get('/predict/analysis', { params: { section_id: sectionId, horizon } }),
}
