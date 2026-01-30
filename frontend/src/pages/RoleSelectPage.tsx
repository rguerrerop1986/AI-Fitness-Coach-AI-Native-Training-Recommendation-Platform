import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../contexts/AuthContext'
import { useClientAuth } from '../contexts/ClientAuthContext'
import { Users, User } from 'lucide-react'

/**
 * Landing page at "/" – role selector or redirect if already authenticated.
 */
export default function RoleSelectPage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { user, loading: coachLoading } = useAuth()
  const { client, loading: clientLoading } = useClientAuth()

  const loading = coachLoading || clientLoading

  useEffect(() => {
    if (loading) return
    if (user) {
      navigate('/dashboard', { replace: true })
      return
    }
    if (client) {
      navigate('/client/dashboard', { replace: true })
      return
    }
  }, [user, client, loading, navigate])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400" />
      </div>
    )
  }

  // If we have a session, we're redirecting in useEffect; show nothing briefly
  if (user || client) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400" />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100 text-center mb-10">
        {t('landing.title')}
      </h1>
      <div className="w-full max-w-md grid gap-4 sm:grid-cols-2 sm:gap-6">
        <button
          type="button"
          onClick={() => navigate('/login')}
          className="relative flex flex-col items-center rounded-xl border-2 border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 p-6 sm:p-8 text-left shadow-sm transition hover:border-primary-500 dark:hover:border-primary-400 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
        >
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 mb-4">
            <Users className="h-7 w-7" />
          </span>
          <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {t('landing.coach')}
          </span>
          <span className="mt-2 text-sm text-gray-500 dark:text-gray-400 text-center">
            {t('landing.coachDescription')}
          </span>
        </button>
        <button
          type="button"
          onClick={() => navigate('/client/login')}
          className="relative flex flex-col items-center rounded-xl border-2 border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 p-6 sm:p-8 text-left shadow-sm transition hover:border-primary-500 dark:hover:border-primary-400 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
        >
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 mb-4">
            <User className="h-7 w-7" />
          </span>
          <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {t('landing.client')}
          </span>
          <span className="mt-2 text-sm text-gray-500 dark:text-gray-400 text-center">
            {t('landing.clientDescription')}
          </span>
        </button>
      </div>
    </div>
  )
}
