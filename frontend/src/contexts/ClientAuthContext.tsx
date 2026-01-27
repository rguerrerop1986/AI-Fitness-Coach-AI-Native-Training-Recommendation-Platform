import React, { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../lib/api'

interface Client {
  id: number
  name: string
  email: string
}

interface ClientAuthContextType {
  client: Client | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
}

const ClientAuthContext = createContext<ClientAuthContextType | undefined>(undefined)

export function ClientAuthProvider({ children }: { children: React.ReactNode }) {
  const [client, setClient] = useState<Client | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('client_access_token')
    const clientData = localStorage.getItem('client_info')
    
    if (token && clientData) {
      try {
        setClient(JSON.parse(clientData))
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`
      } catch (error) {
        console.error('Error parsing client data:', error)
        localStorage.removeItem('client_access_token')
        localStorage.removeItem('client_refresh_token')
        localStorage.removeItem('client_info')
      }
    }
    setLoading(false)
  }, [])

  const login = async (username: string, password: string) => {
    try {
      // Use unified auth endpoint with client-specific serializer
      const response = await api.post('/auth/token/client/', {
        username,
        password
      })
      
      const { client: clientData, access, refresh } = response.data
      
      localStorage.setItem('client_access_token', access)
      localStorage.setItem('client_refresh_token', refresh)
      localStorage.setItem('client_info', JSON.stringify(clientData))
      
      api.defaults.headers.common['Authorization'] = `Bearer ${access}`
      setClient(clientData)
    } catch (error) {
      console.error('Client login error:', error)
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('client_access_token')
    localStorage.removeItem('client_refresh_token')
    localStorage.removeItem('client_info')
    delete api.defaults.headers.common['Authorization']
    setClient(null)
  }

  const refreshToken = async () => {
    try {
      const refresh = localStorage.getItem('client_refresh_token')
      if (!refresh) {
        throw new Error('No refresh token')
      }

      // Use unified token refresh endpoint
      const response = await api.post('/auth/token/refresh/', {
        refresh: refresh
      })
      
      const { access, refresh: newRefresh } = response.data
      
      localStorage.setItem('client_access_token', access)
      localStorage.setItem('client_refresh_token', newRefresh)
      api.defaults.headers.common['Authorization'] = `Bearer ${access}`
    } catch (error) {
      console.error('Token refresh error:', error)
      logout()
      throw error
    }
  }

  return (
    <ClientAuthContext.Provider value={{ client, loading, login, logout, refreshToken }}>
      {children}
    </ClientAuthContext.Provider>
  )
}

export function useClientAuth() {
  const context = useContext(ClientAuthContext)
  if (context === undefined) {
    throw new Error('useClientAuth must be used within a ClientAuthProvider')
  }
  return context
}
