import axios from 'axios'

// Default: relative /api so requests go to the same host that served the page (works from other devices on LAN; Vite proxies to backend in dev)
// Set VITE_API_URL only when the API is on a different host (e.g. production API server)
const API_BASE_URL = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || '/api'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    // Check for coach/assistant token first
    const coachToken = localStorage.getItem('access_token')
    // Then check for client token
    const clientToken = localStorage.getItem('client_access_token')
    
    if (coachToken) {
      config.headers.Authorization = `Bearer ${coachToken}`
    } else if (clientToken) {
      config.headers.Authorization = `Bearer ${clientToken}`
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle token refresh and errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Don't try to refresh if there's no original request (network error, etc.)
    if (!error.config) {
      return Promise.reject(error)
    }

    const originalRequest = error.config

    // If error is 401 and we haven't already retried
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        // Try to refresh coach token
        const coachRefreshToken = localStorage.getItem('refresh_token')
        if (coachRefreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
            refresh: coachRefreshToken,
          })
          const { access, refresh } = response.data
          localStorage.setItem('access_token', access)
          localStorage.setItem('refresh_token', refresh)
          originalRequest.headers.Authorization = `Bearer ${access}`
          return api(originalRequest)
        }

        // Try to refresh client token (uses same endpoint as coach)
        const clientRefreshToken = localStorage.getItem('client_refresh_token')
        if (clientRefreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
            refresh: clientRefreshToken,
          })
          const { access, refresh } = response.data
          localStorage.setItem('client_access_token', access)
          localStorage.setItem('client_refresh_token', refresh)
          originalRequest.headers.Authorization = `Bearer ${access}`
          return api(originalRequest)
        }
      } catch (refreshError) {
        // Refresh failed: clear all auth state and always redirect to home
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        localStorage.removeItem('client_access_token')
        localStorage.removeItem('client_refresh_token')
        localStorage.removeItem('client_info')
        if (typeof window !== 'undefined') {
          window.location.replace('/')
        }
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default api
