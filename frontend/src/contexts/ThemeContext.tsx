import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'

type Theme = 'light' | 'dark'

interface ThemeContextType {
  theme: Theme
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    // Check localStorage first
    const stored = localStorage.getItem('theme') as Theme | null
    if (stored === 'light' || stored === 'dark') {
      return stored
    }
    
    // Fallback to system preference
    if (typeof window !== 'undefined') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      return prefersDark ? 'dark' : 'light'
    }
    
    return 'light'
  })

  useEffect(() => {
    const root = document.documentElement
    const body = document.body
    
    // Apply theme class immediately
    if (theme === 'dark') {
      root.classList.add('dark')
      body.classList.add('dark')
    } else {
      root.classList.remove('dark')
      body.classList.remove('dark')
    }
    
    // Persist to localStorage
    localStorage.setItem('theme', theme)
  }, [theme])

  // Listen to system preference changes (optional)
  useEffect(() => {
    if (typeof window === 'undefined') return
    
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = (e: MediaQueryListEvent) => {
      // Only auto-switch if user hasn't manually set a preference
      const stored = localStorage.getItem('theme')
      if (!stored) {
        setTheme(e.matches ? 'dark' : 'light')
      }
    }
    
    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange)
      return () => mediaQuery.removeEventListener('change', handleChange)
    } else {
      // Fallback for older browsers
      mediaQuery.addListener(handleChange)
      return () => mediaQuery.removeListener(handleChange)
    }
  }, [])

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light')
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}
