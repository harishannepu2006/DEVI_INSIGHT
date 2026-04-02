import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

// Add auth token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth
export const authAPI = {
  callback: (data) => api.post('/auth/callback', data),
  me: () => api.get('/auth/me'),
  refresh: (refresh_token) => api.post('/auth/refresh', { refresh_token }),
}

// Repositories
export const repoAPI = {
  submit: (url, branch) => api.post('/repositories/submit', { url, branch }),
  submitSnippet: (code, language, filename) =>
    api.post('/repositories/snippet', { code, language, filename }),
  list: () => api.get('/repositories'),
  get: (id) => api.get(`/repositories/${id}`),
  delete: (id) => api.delete(`/repositories/${id}`),
  getInsights: (id) => api.get(`/repositories/${id}/insights`),
}

// Analysis
export const analysisAPI = {
  list: () => api.get('/analysis'),
  get: (id) => api.get(`/analysis/${id}`),
  dashboard: () => api.get('/analysis/dashboard'),
  history: (id) => api.get(`/analysis/${id}/history`),
}

// Bugs
export const bugsAPI = {
  byAnalysis: (analysisId, filters = {}) => {
    const params = new URLSearchParams()
    if (filters.severity) params.set('severity', filters.severity)
    if (filters.category) params.set('category', filters.category)
    return api.get(`/bugs/analysis/${analysisId}?${params}`)
  },
  get: (id) => api.get(`/bugs/${id}`),
  resolve: (id) => api.patch(`/bugs/${id}/resolve`),
  stats: (analysisId) => api.get(`/bugs/stats/${analysisId}`),
}

// Insights
export const insightsAPI = {
  byAnalysis: (analysisId) => api.get(`/insights/analysis/${analysisId}`),
  get: (id) => api.get(`/insights/${id}`),
}

// Reports
export const reportsAPI = {
  generate: (analysisId, reportType, format) =>
    api.post('/reports/generate', {
      analysis_id: analysisId,
      report_type: reportType,
      format
    }),
  downloadUrl: (reportId, filename) => `${API_BASE}/reports/download/${reportId}/${filename}`,
  list: () => api.get('/reports'),
}

// Chat
export const chatAPI = {
  send: (bugId, message) => api.post(`/chat/bug/${bugId}`, { message }),
  history: (bugId) => api.get(`/chat/bug/${bugId}/history`),
}

export default api
