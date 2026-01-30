import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'
import { useTranslation } from 'react-i18next'
import { useRole } from '../auth/useRole'
import { UserRole } from '../auth/roles'
import { 
  Home, 
  Users, 
  Apple, 
  Dumbbell, 
  Calendar, 
  FileText,
  LogOut,
  Menu,
  X,
  Clock,
  Moon,
  Sun,
  Globe
} from 'lucide-react'
import { useState } from 'react'

export default function Layout() {
  const { user, logout } = useAuth()
  const { role } = useRole()
  const { theme, toggleTheme } = useTheme()
  const location = useLocation()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [langMenuOpen, setLangMenuOpen] = useState(false)
  const { t, i18n: i18nInstance } = useTranslation()

  // Define navigation items with allowed roles
  const allNavigationItems = [
    { name: t('navigation.dashboard'), href: '/dashboard', icon: Home, roles: ['coach', 'assistant', 'client'] as UserRole[] },
    { name: t('navigation.plans'), href: '/plans', icon: Calendar, roles: ['coach', 'assistant', 'client'] as UserRole[] },
    { name: t('navigation.checkIns'), href: '/checkins', icon: FileText, roles: ['coach', 'assistant', 'client'] as UserRole[] },
    { name: t('navigation.appointments'), href: '/appointments', icon: Clock, roles: ['coach', 'assistant', 'client'] as UserRole[] },
    // Coach-only items
    { name: t('navigation.clients'), href: '/clients', icon: Users, roles: ['coach', 'assistant'] as UserRole[] },
    { name: t('navigation.foods'), href: '/foods', icon: Apple, roles: ['coach', 'assistant'] as UserRole[] },
    { name: t('navigation.exercises'), href: '/exercises', icon: Dumbbell, roles: ['coach', 'assistant'] as UserRole[] },
  ]

  // Filter navigation based on current role
  const navigation = allNavigationItems.filter(item => {
    if (!role) return false
    return item.roles.includes(role)
  })

  const handleLanguageChange = (lng: string) => {
    i18nInstance.changeLanguage(lng)
    localStorage.setItem('language', lng)
    setLangMenuOpen(false)
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Mobile sidebar */}
      <div className={`fixed inset-0 z-50 lg:hidden ${sidebarOpen ? 'block' : 'hidden'}`}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75 dark:bg-gray-900 dark:bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        <div className="fixed inset-y-0 left-0 flex w-64 flex-col bg-white dark:bg-gray-800">
          <div className="flex h-16 items-center justify-between px-4">
            <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Fitness Coach</h1>
            <button
              onClick={() => setSidebarOpen(false)}
              className="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
          <nav className="flex-1 space-y-1 px-2 py-4">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md ${
                    isActive
                      ? 'bg-primary-100 dark:bg-primary-900 text-primary-900 dark:text-primary-100'
                      : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-gray-100'
                  }`}
                  onClick={() => setSidebarOpen(false)}
                >
                  <item.icon className="mr-3 h-5 w-5" />
                  {item.name}
                </Link>
              )
            })}
          </nav>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-grow bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
          <div className="flex h-16 items-center px-4">
            <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Fitness Coach</h1>
          </div>
          <nav className="flex-1 space-y-1 px-2 py-4">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md ${
                    isActive
                      ? 'bg-primary-100 dark:bg-primary-900 text-primary-900 dark:text-primary-100'
                      : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-gray-100'
                  }`}
                >
                  <item.icon className="mr-3 h-5 w-5" />
                  {item.name}
                </Link>
              )
            })}
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <div className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
          <button
            type="button"
            className="-m-2.5 p-2.5 text-gray-700 dark:text-gray-300 lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-6 w-6" />
          </button>

          <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
            <div className="flex flex-1" />
            <div className="flex items-center gap-x-4 lg:gap-x-6">
              <div className="hidden lg:block lg:h-6 lg:w-px lg:bg-gray-200 dark:lg:bg-gray-700" />
              <div className="flex items-center gap-x-4">
                <button
                  onClick={toggleTheme}
                  className="p-2 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  title={theme === 'dark' ? t('theme.switchToLight') : t('theme.switchToDark')}
                >
                  {theme === 'dark' ? (
                    <Sun className="h-5 w-5" />
                  ) : (
                    <Moon className="h-5 w-5" />
                  )}
                </button>
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setLangMenuOpen(!langMenuOpen)}
                    className="flex items-center gap-1 p-2 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    title={t('language.label')}
                  >
                    <Globe className="h-5 w-5" />
                    <span className="text-sm font-medium uppercase">{i18nInstance.language?.slice(0, 2) || 'es'}</span>
                  </button>
                  {langMenuOpen && (
                    <>
                      <div className="fixed inset-0 z-10" onClick={() => setLangMenuOpen(false)} />
                      <div className="absolute right-0 mt-1 w-36 rounded-md bg-white dark:bg-gray-800 shadow-lg ring-1 ring-black ring-opacity-5 z-20">
                        <button
                          onClick={() => handleLanguageChange('es')}
                          className={`block w-full text-left px-4 py-2 text-sm rounded-t-md ${i18nInstance.language?.startsWith('es') ? 'bg-primary-100 dark:bg-primary-900 text-primary-900 dark:text-primary-100 font-medium' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
                        >
                          {t('language.es')}
                        </button>
                        <button
                          onClick={() => handleLanguageChange('en')}
                          className={`block w-full text-left px-4 py-2 text-sm rounded-b-md ${i18nInstance.language?.startsWith('en') ? 'bg-primary-100 dark:bg-primary-900 text-primary-900 dark:text-primary-100 font-medium' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
                        >
                          {t('language.en')}
                        </button>
                      </div>
                    </>
                  )}
                </div>
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  {user?.first_name} {user?.last_name}
                </span>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-x-2 text-sm text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
                >
                  <LogOut className="h-4 w-4" />
                  {t('auth.logout')}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="py-6">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
