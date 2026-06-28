import axios from 'axios'
import { useAuthStore } from '../store/auth'

const getApiUrl = () => {
  if (import.meta.env.VITE_API_URL === '/api') {
    return '/api'
  }
  return `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api`
}

export const api = axios.create({
  baseURL: getApiUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.setState({ token: null })
      localStorage.removeItem('token')
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { username: email, password }),
  signup: (email: string, username: string, password: string) =>
    api.post('/auth/signup', { email, username, password }),
  me: () => api.get('/auth/me'),
}

export const bankrollApi = {
  initialize: (amount: number) =>
    api.post('/bankroll/initialize', { initial_amount: amount }),
  getCurrent: () => api.get('/bankroll/current'),
  update: (balance: number) =>
    api.put('/bankroll/update', { current_balance: balance }),
}

export const predictionApi = {
  submit: (data: any) => api.post('/predictions', data),
  list: (skip?: number, limit?: number) =>
    api.get('/predictions', { params: { skip, limit } }),
  get: (id: string) => api.get(`/predictions/${id}`),
}

export const kellyApi = {
  calculate: (probability: number, odds: number) =>
    api.post('/kelly/calculate', { win_probability: probability, decimal_odds: odds }),
  suggestStake: (probability: number, odds: number, bankroll: number) =>
    api.post('/kelly/suggest-stake', {
      win_probability: probability,
      decimal_odds: odds,
      bankroll,
    }),
}

export const betApi = {
  place: (data: any) => api.post('/place-bet', data),
  get: (id: string) => api.get(`/place-bet/${id}`),
  transition: (id: string, newStatus: string) =>
    api.post(`/place-bet/${id}/transition`, { new_status: newStatus }),
}

export const positionApi = {
  active: () => api.get('/positions/active'),
  all: (status?: string) => api.get('/positions/all', { params: { status } }),
  summary: () => api.get('/positions/summary'),
}

export const settlementApi = {
  settle: (betId: string, outcome: string, actualReturn: number) =>
    api.post(`/settle/${betId}`, { actual_outcome: outcome, actual_return: actualReturn }),
  void: (betId: string) => api.post(`/settle/${betId}/void`),
}

export const auditApi = {
  list: (action?: string, daysBack?: number) =>
    api.get('/audit-log', { params: { action, days_back: daysBack } }),
  getByEntity: (type: string, id: string) =>
    api.get(`/audit-log/entity/${type}/${id}`),
  summary: () => api.get('/audit-log/summary'),
}

export const portfolioApi = {
  simulate: (data: any) =>
    api.post('/portfolio/simulate', data),
  allocate: (data: any) =>
    api.post('/portfolio/allocation', data),
  assessRegime: (data: any) =>
    api.post('/portfolio/regime', data),
  health: () =>
    api.get('/portfolio/health'),
}
