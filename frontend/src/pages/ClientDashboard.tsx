import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useTheme } from '../contexts/ThemeContext'
import { 
  User, 
  Apple, 
  Dumbbell, 
  TrendingUp, 
  Download, 
  LogOut,
  Scale,
  Target,
  Clock,
  Moon,
  Sun,
  ClipboardList
} from 'lucide-react'
import { api } from '../lib/api'

interface ClientData {
  id: number
  first_name: string
  last_name: string
  email: string
  height_cm: number
  initial_weight_kg: number
  latest_measurement: {
    date: string
    weight_kg: number
    body_fat_pct: number | null
    chest_cm: number | null
    waist_cm: number | null
    hips_cm: number | null
    bicep_cm: number | null
    thigh_cm: number | null
    calf_cm: number | null
  } | null
  active_diet_plan: {
    id: number
    title: string
    goal: string
    daily_calories: number
    version: number
    assigned_date: string
  } | null
  active_workout_plan: {
    id: number
    title: string
    goal: string
    version: number
    assigned_date: string
  } | null
}

export default function ClientDashboard() {
  const { theme, toggleTheme } = useTheme()
  const { t, i18n: i18nInstance } = useTranslation()
  const [clientData, setClientData] = useState<ClientData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    fetchClientData()
  }, [])

  const fetchClientData = async () => {
    try {
      const response = await api.get('/client/dashboard/')
      setClientData(response.data)
    } catch (error: any) {
      console.error('Error fetching client data:', error)
      if (error.response?.status === 401) {
        // Token expired or invalid, redirect to root (role selector)
        localStorage.removeItem('client_access_token')
        localStorage.removeItem('client_refresh_token')
        localStorage.removeItem('client_info')
        navigate('/')
        return
      }
      setError(t('clientPortal.dashboardLoadFailed'))
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('client_access_token')
    localStorage.removeItem('client_refresh_token')
    localStorage.removeItem('client_info')
    delete api.defaults.headers.common['Authorization']
    navigate('/')
  }

  const downloadCurrentPlanPdf = async () => {
    try {
      const response = await api.get('/client/current-plan/pdf/', {
        responseType: 'blob'
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'mi_plan.pdf')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      console.error('Error downloading plan:', err)
      setError(err.response?.data?.error || t('clientPortal.downloadPdfFailed'))
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">{error}</div>
        <button
          onClick={fetchClientData}
          className="bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700"
        >
          {t('common.tryAgain')}
        </button>
      </div>
    )
  }

  if (!clientData) {
    return <div>{t('clientPortal.dashboardLoadFailed')}</div>
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <User className="h-8 w-8 text-primary-600 dark:text-primary-400 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {t('clientPortal.welcome', { name: clientData.first_name })}
                </h1>
                <p className="text-gray-600 dark:text-gray-400">{t('clientPortal.dashboardSubtitle')}</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex rounded-md border border-gray-300 dark:border-gray-600 overflow-hidden">
                <button
                  type="button"
                  onClick={() => { i18nInstance.changeLanguage('es'); localStorage.setItem('language', 'es'); }}
                  className={`px-2 py-1 text-sm font-medium ${i18nInstance.language?.startsWith('es') ? 'bg-primary-600 text-white dark:bg-primary-500' : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
                >
                  ES
                </button>
                <button
                  type="button"
                  onClick={() => { i18nInstance.changeLanguage('en'); localStorage.setItem('language', 'en'); }}
                  className={`px-2 py-1 text-sm font-medium ${i18nInstance.language?.startsWith('en') ? 'bg-primary-600 text-white dark:bg-primary-500' : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
                >
                  EN
                </button>
              </div>
              <button
                onClick={toggleTheme}
                className="p-2 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                title={theme === 'dark' ? t('theme.switchToLight') : t('theme.switchToDark')}
              >
                {theme === 'dark' ? (
                  <Sun className="h-5 w-5" />
                ) : (
                  <Moon className="h-5 w-5" />
                )}
              </button>
              <button
                onClick={() => navigate('/client/rutina-de-hoy')}
                className="flex items-center text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
              >
                <Dumbbell className="h-5 w-5 mr-2" />
                Rutina de hoy
              </button>
              <button
                onClick={() => navigate('/client/daily-log')}
                className="flex items-center text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
              >
                <ClipboardList className="h-5 w-5 mr-2" />
                Registro diario
              </button>
              <button
                onClick={() => navigate('/client/appointments')}
                className="flex items-center text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
              >
                <Clock className="h-5 w-5 mr-2" />
                {t('clientPortal.appointments')}
              </button>
              <button
                onClick={handleLogout}
                className="flex items-center text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
              >
                <LogOut className="h-5 w-5 mr-2" />
                {t('clientPortal.logout')}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Quick action: Daily log */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/client/daily-log')}
            className="card w-full sm:w-auto flex items-center gap-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-left"
          >
            <ClipboardList className="h-8 w-8 text-primary-600 dark:text-primary-400 flex-shrink-0" />
            <div>
              <p className="font-medium text-gray-900 dark:text-gray-100">Registro diario</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Registra tu entrenamiento y alimentación de hoy</p>
            </div>
          </button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Scale className="h-8 w-8 text-primary-600 dark:text-primary-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                    {t('clientPortal.currentWeight')}
                  </dt>
                  <dd className="text-lg font-medium text-gray-900 dark:text-gray-100">
                    {clientData.latest_measurement?.weight_kg || clientData.initial_weight_kg} kg
                  </dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Target className="h-8 w-8 text-success-600 dark:text-success-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                    {t('clientPortal.height')}
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {clientData.height_cm} cm
                  </dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Apple className="h-8 w-8 text-warning-600 dark:text-warning-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                    {t('clientPortal.activeDietPlan')}
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {clientData.active_diet_plan ? 'Yes' : 'None'}
                  </dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Dumbbell className="h-8 w-8 text-danger-600 dark:text-danger-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                    {t('clientPortal.activeWorkoutPlan')}
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {clientData.active_workout_plan ? 'Yes' : 'None'}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        {/* Plans Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Diet Plan */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 flex items-center">
                <Apple className="h-6 w-6 text-warning-600 dark:text-warning-400 mr-2" />
                {t('clientPortal.dietPlan')}
              </h2>
            </div>
            
            {clientData.active_diet_plan ? (
              <div>
                <div className="mb-4">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                    {clientData.active_diet_plan.title}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    {t('clientPortal.goal')}: {clientData.active_diet_plan.goal}
                  </p>
                  <p className="text-gray-600 dark:text-gray-400">
                    {t('clientPortal.dailyCalories')}: {clientData.active_diet_plan.daily_calories} {t('clientPortal.kcal')}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {t('clientPortal.assigned')}: {new Date(clientData.active_diet_plan.assigned_date).toLocaleDateString()}
                  </p>
                </div>
                
                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={() => navigate('/client/plan')}
                    className="flex items-center bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700 dark:bg-primary-500 dark:hover:bg-primary-600"
                  >
                    {t('clientPortal.viewPlan')}
                  </button>
                  <button
                    onClick={downloadCurrentPlanPdf}
                    className="flex items-center bg-warning-600 text-white px-4 py-2 rounded hover:bg-warning-700 dark:bg-warning-500 dark:hover:bg-warning-600"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    {t('clientPortal.downloadPdf')}
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <Apple className="h-12 w-12 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400">{t('clientPortal.noDietPlan')}</p>
                <p className="text-sm text-gray-400 dark:text-gray-500">{t('clientPortal.contactCoach')}</p>
              </div>
            )}
          </div>

          {/* Workout Plan */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 flex items-center">
                <Dumbbell className="h-6 w-6 text-danger-600 dark:text-danger-400 mr-2" />
                {t('clientPortal.workoutPlan')}
              </h2>
            </div>
            
            {clientData.active_workout_plan ? (
              <div>
                <div className="mb-4">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                    {clientData.active_workout_plan.title}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    {t('clientPortal.goal')}: {clientData.active_workout_plan.goal}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {t('clientPortal.assigned')}: {new Date(clientData.active_workout_plan.assigned_date).toLocaleDateString()}
                  </p>
                </div>
                
                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={() => navigate('/client/plan')}
                    className="flex items-center bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700 dark:bg-primary-500 dark:hover:bg-primary-600"
                  >
                    {t('clientPortal.viewPlan')}
                  </button>
                  <button
                    onClick={downloadCurrentPlanPdf}
                    className="flex items-center bg-danger-600 text-white px-4 py-2 rounded hover:bg-danger-700 dark:bg-danger-500 dark:hover:bg-danger-600"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    {t('clientPortal.downloadPdf')}
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <Dumbbell className="h-12 w-12 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400">{t('clientPortal.noWorkoutPlan')}</p>
                <p className="text-sm text-gray-400 dark:text-gray-500">{t('clientPortal.contactCoach')}</p>
              </div>
            )}
          </div>
        </div>

        {/* Measurements Section */}
        {clientData.latest_measurement && (
          <div className="mt-8">
            <div className="card">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
                <TrendingUp className="h-6 w-6 text-success-600 dark:text-success-400 mr-2" />
                {t('clientPortal.latestMeasurements')}
                <span className="text-sm font-normal text-gray-500 dark:text-gray-400 ml-2">
                  ({new Date(clientData.latest_measurement.date).toLocaleDateString()})
                </span>
              </h2>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded">
                  <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {clientData.latest_measurement.weight_kg}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">{t('clientPortal.weightKg')}</div>
                </div>
                
                {clientData.latest_measurement.body_fat_pct && (
                  <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded">
                    <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                      {clientData.latest_measurement.body_fat_pct}%
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">{t('clientPortal.bodyFat')}</div>
                  </div>
                )}
                
                {clientData.latest_measurement.chest_cm && (
                  <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded">
                    <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                      {clientData.latest_measurement.chest_cm}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">{t('clientPortal.chestCm')}</div>
                  </div>
                )}
                
                {clientData.latest_measurement.waist_cm && (
                  <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded">
                    <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                      {clientData.latest_measurement.waist_cm}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">{t('clientPortal.waistCm')}</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
