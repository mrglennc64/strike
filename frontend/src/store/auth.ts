import { create } from 'zustand'
import { api } from '../api/client'

interface AuthState {
  token: string | null
  user: any | null
  isLoading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, username: string, password: string) => Promise<void>
  logout: () => void
  setToken: (token: string | null) => void
  loadToken: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem('token'),
  user: null,
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await api.post('/auth/login', {
        username: email,
        password,
      })
      const token = response.data.access_token
      localStorage.setItem('token', token)
      set({ token, isLoading: false })
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Login failed'
      set({ error: message, isLoading: false })
      throw error
    }
  },

  signup: async (email: string, username: string, password: string) => {
    set({ isLoading: true, error: null })
    try {
      await api.post('/auth/signup', { email, username, password })
      const response = await api.post('/auth/login', {
        username: email,
        password,
      })
      const token = response.data.access_token
      localStorage.setItem('token', token)
      set({ token, isLoading: false })
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Signup failed'
      set({ error: message, isLoading: false })
      throw error
    }
  },

  logout: () => {
    localStorage.removeItem('token')
    set({ token: null, user: null })
  },

  setToken: (token: string | null) => {
    if (token) {
      localStorage.setItem('token', token)
    } else {
      localStorage.removeItem('token')
    }
    set({ token })
  },

  loadToken: () => {
    const token = localStorage.getItem('token')
    set({ token })
  },
}))
