import React, { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../lib/api'

interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: 'coach' | 'assistant' | 'client'
  phone: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    const userData = localStorage.getItem('user')
    
    if (token && userData) {
      try {
        setUser(JSON.parse(userData))
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`
      } catch (error) {
        console.error('Error parsing user data:', error)
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
        localStorage.removeItem('refresh_token')
      }
    }
    setLoading(false)
  }, [])

  const login = async (username: string, password: string) => {
    try {
      const response = await api.post('/auth/login/', {
        username,
        password
      })
      
      const { user: userData, tokens } = response.data
      
      // Clear client portal tokens so coach session is isolated
      localStorage.removeItem('client_access_token')
      localStorage.removeItem('client_refresh_token')
      localStorage.removeItem('client_info')
      
      localStorage.setItem('access_token', tokens.access)
      localStorage.setItem('refresh_token', tokens.refresh)
      localStorage.setItem('user', JSON.stringify(userData))
      
      api.defaults.headers.common['Authorization'] = `Bearer ${tokens.access}`
      setUser(userData)
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    delete api.defaults.headers.common['Authorization']
    setUser(null)
  }

  const refreshToken = async () => {
    try {
      const refresh = localStorage.getItem('refresh_token')
      if (!refresh) {
        throw new Error('No refresh token')
      }

      const response = await api.post('/auth/refresh/', {
        refresh_token: refresh
      })
      
      const { access, refresh: newRefresh } = response.data
      
      localStorage.setItem('access_token', access)
      localStorage.setItem('refresh_token', newRefresh)
      api.defaults.headers.common['Authorization'] = `Bearer ${access}`
    } catch (error) {
      console.error('Token refresh error:', error)
      logout()
      throw error
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshToken }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
