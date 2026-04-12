import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useTheme } from '../contexts/ThemeContext'
import {
  User,
  Apple,
  Dumbbell,
  LogOut,
  Scale,
  Target,
  Clock,
  Moon,
  Sun,
  ClipboardList,
  Video,
  MessageSquare
} from 'lucide-react'
import { useClientAuth } from '../contexts/ClientAuthContext'
import { api } from '../lib/api'

/** Dashboard V2 payload from GET /api/client/dashboard/ */
interface DashboardClient {
  id: number
  name: string
  current_weight: number | null
  height_cm: number | null
}

interface DietFood {
  id: number
  name: string
  quantity: number
  unit: string
  calories: number | null
}

interface DietMeal {
  meal_type: string
  title: string
  foods: DietFood[]
}

interface DietPlanActive {
  title: string
  goal: string
  coach_message: string
  total_calories: number | null
  meals: DietMeal[]
}

interface TrainingExercise {
  name: string
  sets: number
  reps: number
  order: number
  rest_seconds?: number | null
  notes?: string
}

interface RecommendedVideo {
  title: string
  duration_minutes: number | null
}

interface TrainingPlanActive {
  recommendation_type: string
  training_group: string
  training_group_label: string
  modality?: string
  intensity_level?: number | null
  reasoning_summary: string
  coach_message: string
  recommended_video: RecommendedVideo | null
  exercises: TrainingExercise[]
}

/** Readiness check-in (today) from API or form state — matches DailyReadinessCheckin from backend */
export interface ReadinessFormData {
  sleep_quality?: number | null
  diet_adherence_yesterday?: number | null
  motivation_today?: number | null
  energy_level?: number | null
  stress_level?: number | null
  muscle_soreness?: number | null
  readiness_to_train?: number | null
  mood?: number | null
  hydration_level?: number | null
  yesterday_training_intensity?: number | null
  slept_poorly?: boolean
  ate_poorly_yesterday?: boolean
  feels_100_percent?: boolean
  wants_video_today?: boolean
  preferred_training_mode?: 'insanity' | 'hybrid' | 'gym_strength' | 'mobility_recovery' | 'auto'
  comments?: string
}

const DEFAULT_READINESS_FORM: ReadinessFormData = {
  sleep_quality: 7,
  diet_adherence_yesterday: 7,
  motivation_today: 7,
  energy_level: 7,
  stress_level: 5,
  muscle_soreness: 3,
  readiness_to_train: 7,
  mood: 7,
  hydration_level: 7,
  yesterday_training_intensity: 5,
  slept_poorly: false,
  ate_poorly_yesterday: false,
  feels_100_percent: false,
  wants_video_today: false,
  preferred_training_mode: 'auto',
  comments: '',
}

export interface DashboardData {
  client: DashboardClient
  today: string
  diet_plan_active: DietPlanActive | null
  training_plan_active: TrainingPlanActive | null
  readiness_required: boolean
  has_today_readiness: boolean
  readiness: ReadinessFormData | null
  has_recommendation_today: boolean
}

export default function ClientDashboard() {
  const { theme, toggleTheme } = useTheme()
  const { t, i18n: i18nInstance } = useTranslation()
  const { logout } = useClientAuth()
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [submittingReadiness, setSubmittingReadiness] = useState(false)
  const [readinessForm, setReadinessForm] = useState<ReadinessFormData>(DEFAULT_READINESS_FORM)
  const navigate = useNavigate()

  /** Build form state from dashboard: client + today's readiness from API (DailyReadinessCheckin) or defaults */
  useEffect(() => {
    if (!dashboard) return
    const fromApi = dashboard.readiness
    if (fromApi) {
      setReadinessForm({
        ...DEFAULT_READINESS_FORM,
        sleep_quality: fromApi.sleep_quality ?? DEFAULT_READINESS_FORM.sleep_quality,
        diet_adherence_yesterday: fromApi.diet_adherence_yesterday ?? DEFAULT_READINESS_FORM.diet_adherence_yesterday,
        motivation_today: fromApi.motivation_today ?? DEFAULT_READINESS_FORM.motivation_today,
        energy_level: fromApi.energy_level ?? DEFAULT_READINESS_FORM.energy_level,
        stress_level: fromApi.stress_level ?? DEFAULT_READINESS_FORM.stress_level,
        muscle_soreness: fromApi.muscle_soreness ?? DEFAULT_READINESS_FORM.muscle_soreness,
        readiness_to_train: fromApi.readiness_to_train ?? DEFAULT_READINESS_FORM.readiness_to_train,
        mood: fromApi.mood ?? DEFAULT_READINESS_FORM.mood,
        hydration_level: fromApi.hydration_level ?? DEFAULT_READINESS_FORM.hydration_level,
        yesterday_training_intensity: fromApi.yesterday_training_intensity ?? DEFAULT_READINESS_FORM.yesterday_training_intensity,
        slept_poorly: fromApi.slept_poorly ?? DEFAULT_READINESS_FORM.slept_poorly,
        ate_poorly_yesterday: fromApi.ate_poorly_yesterday ?? DEFAULT_READINESS_FORM.ate_poorly_yesterday,
        feels_100_percent: fromApi.feels_100_percent ?? DEFAULT_READINESS_FORM.feels_100_percent,
        wants_video_today: fromApi.wants_video_today ?? DEFAULT_READINESS_FORM.wants_video_today,
        preferred_training_mode: (fromApi.preferred_training_mode as ReadinessFormData['preferred_training_mode']) ?? DEFAULT_READINESS_FORM.preferred_training_mode,
        comments: fromApi.comments ?? DEFAULT_READINESS_FORM.comments,
      })
    } else {
      setReadinessForm({ ...DEFAULT_READINESS_FORM })
    }
  }, [dashboard])

  const fetchClientData = useCallback(async () => {
    setError('')
    setLoading(true)
    try {
      const response = await api.get<DashboardData>('/client/dashboard/')
      setDashboard(response.data)
    } catch (err: any) {
      console.error('Error fetching client dashboard:', err)
      if (err.response?.status === 401) {
        logout()
        navigate('/', { replace: true })
        return
      }
      if (err.response?.status === 503 && err.response?.data?.error === 'insufficient_catalog') {
        const detail = err.response?.data?.detail || err.response?.data?.catalog
        setError(detail || t('clientPortal.dashboardLoadFailed'))
        return
      }
      setError(t('clientPortal.dashboardLoadFailed'))
    } finally {
      setLoading(false)
    }
  }, [t, logout, navigate])

  useEffect(() => {
    fetchClientData()
  }, [fetchClientData])

  const handleLogout = () => {
    logout()
    navigate('/', { replace: true })
  }

  const clientName = dashboard?.client?.name?.split(' ')[0] ?? ''

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-10 w-10 border-2 border-primary-600 border-t-transparent" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-md mx-auto text-center py-16 px-4">
        <p className="text-red-600 dark:text-red-400 mb-6">{error}</p>
        <button
          type="button"
          onClick={fetchClientData}
          className="bg-primary-600 text-white px-5 py-2.5 rounded-lg hover:bg-primary-700 dark:bg-primary-500 dark:hover:bg-primary-600"
        >
          {t('common.tryAgain')}
        </button>
      </div>
    )
  }

  if (!dashboard) {
    return (
      <div className="max-w-md mx-auto text-center py-16 px-4">
        <p className="text-gray-600 dark:text-gray-400 mb-6">{t('clientPortal.dashboardLoadFailed')}</p>
        <button
          type="button"
          onClick={fetchClientData}
          className="bg-primary-600 text-white px-5 py-2.5 rounded-lg hover:bg-primary-700"
        >
          {t('common.tryAgain')}
        </button>
      </div>
    )
  }

  const { client, diet_plan_active, training_plan_active, readiness_required } = dashboard
  const hasDiet = diet_plan_active != null
  const hasTraining = training_plan_active != null
  const emptyRecommendations = !hasDiet && !hasTraining
  const needsReadiness = readiness_required === true
  const showPlans = !needsReadiness

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
                  {t('clientPortal.welcome', { name: clientName })}
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
                {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
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
            type="button"
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

        {/* Readiness / check-in diario: mostrar antes de planes si falta */}
        {needsReadiness && (
          <div className="mb-8">
            <div className="card">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Check-in diario — ¿Cómo estás hoy?
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Antes de generar tu plan de hoy, cuéntanos cómo dormiste, tu energía y cómo te sientes. Así personalizamos dieta y entrenamiento.
              </p>
              <form
                className="space-y-4"
                onSubmit={async (e) => {
                  e.preventDefault()
                  setSubmittingReadiness(true)
                  setError('')
                  try {
                    await api.post('/client/readiness/today/', readinessForm)
                    await fetchClientData()
                  } catch (err: any) {
                    console.error('Error saving readiness', err)
                    setError(err.response?.data?.detail || 'No se pudo guardar tu check-in. Inténtalo de nuevo.')
                  } finally {
                    setSubmittingReadiness(false)
                  }
                }}
              >
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[
                    { key: 'sleep_quality', label: 'Calidad de sueño (1-10)' },
                    { key: 'energy_level', label: 'Energía actual (1-10)' },
                    { key: 'motivation_today', label: 'Motivación hoy (1-10)' },
                    { key: 'diet_adherence_yesterday', label: 'Apego a la dieta ayer (1-10)' },
                    { key: 'stress_level', label: 'Estrés (1-10)' },
                    { key: 'muscle_soreness', label: 'Dolor/fatiga muscular (1-10)' },
                    { key: 'readiness_to_train', label: 'Disposición a entrenar (1-10)' },
                    { key: 'mood', label: 'Estado de ánimo (1-10)' },
                    { key: 'hydration_level', label: 'Hidratación (1-10)' },
                    { key: 'yesterday_training_intensity', label: 'Intensidad del entrenamiento de ayer (1-10)' },
                  ].map(({ key, label }) => (
                    <div key={key}>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{label}</label>
                      <input
                        type="range"
                        min={1}
                        max={10}
                        value={readinessForm[key as keyof ReadinessFormData] ?? 7}
                        onChange={(e) =>
                          setReadinessForm((f) => ({ ...f, [key]: Number(e.target.value) }))
                        }
                        className="w-full h-2 bg-gray-200 dark:bg-gray-600 rounded-lg appearance-none cursor-pointer"
                      />
                      <span className="text-xs text-gray-500 dark:text-gray-400 ml-1">
                        {Number(readinessForm[key as keyof ReadinessFormData] ?? 7)}
                      </span>
                    </div>
                  ))}
                </div>
                <div className="flex flex-wrap gap-4 items-center">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={!!readinessForm.slept_poorly}
                      onChange={(e) => setReadinessForm((f) => ({ ...f, slept_poorly: e.target.checked }))}
                      className="h-4 w-4 text-primary-600 border-gray-300 rounded dark:bg-gray-700"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">Dormí mal / poco</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={!!readinessForm.ate_poorly_yesterday}
                      onChange={(e) => setReadinessForm((f) => ({ ...f, ate_poorly_yesterday: e.target.checked }))}
                      className="h-4 w-4 text-primary-600 border-gray-300 rounded dark:bg-gray-700"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">Ayer comí mal</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={!!readinessForm.feels_100_percent}
                      onChange={(e) => setReadinessForm((f) => ({ ...f, feels_100_percent: e.target.checked }))}
                      className="h-4 w-4 text-primary-600 border-gray-300 rounded dark:bg-gray-700"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">Me siento al 100%</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={!!readinessForm.wants_video_today}
                      onChange={(e) => setReadinessForm((f) => ({ ...f, wants_video_today: e.target.checked }))}
                      className="h-4 w-4 text-primary-600 border-gray-300 rounded dark:bg-gray-700"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">Hoy prefiero video</span>
                  </label>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Modalidad preferida hoy
                  </label>
                  <select
                    value={readinessForm.preferred_training_mode ?? 'auto'}
                    onChange={(e) =>
                      setReadinessForm((f) => ({
                        ...f,
                        preferred_training_mode: e.target.value as ReadinessFormData['preferred_training_mode'],
                      }))
                    }
                    className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  >
                    <option value="auto">Auto (el sistema decide)</option>
                    <option value="insanity">Insanity</option>
                    <option value="hybrid">Híbrido</option>
                    <option value="gym_strength">Fuerza en gym</option>
                    <option value="mobility_recovery">Movilidad / Recovery</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Comentarios (opcional)
                  </label>
                  <textarea
                    rows={3}
                    value={readinessForm.comments ?? ''}
                    onChange={(e) => setReadinessForm((f) => ({ ...f, comments: e.target.value }))}
                    className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    placeholder="Ej: Dormí poco y me siento pesado de piernas. / Hoy tengo energía pero me duele el hombro."
                  />
                </div>
                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={submittingReadiness}
                    className="bg-primary-600 text-white px-5 py-2.5 rounded-lg hover:bg-primary-700 disabled:opacity-60 font-medium"
                  >
                    {submittingReadiness ? 'Generando tu plan...' : 'Generar mi plan de hoy'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {showPlans && (
          <>
        {/* Stats: weight, height (height_cm from backend) */}
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
                    {client.current_weight != null ? `${client.current_weight} kg` : '—'}
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
                  <dd className="text-lg font-medium text-gray-900 dark:text-gray-100">
                    {client.height_cm != null ? `${client.height_cm} cm` : '—'}
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
                    Dieta de hoy
                  </dt>
                  <dd className="text-lg font-medium text-gray-900 dark:text-gray-100">
                    {hasDiet ? diet_plan_active!.title : '—'}
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
                    Entrenamiento de hoy
                  </dt>
                  <dd className="text-lg font-medium text-gray-900 dark:text-gray-100">
                    {hasTraining
                      ? (training_plan_active!.training_group_label || training_plan_active!.recommendation_type)
                      : '—'}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        {/* Daily recommendation cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Diet card */}
          <div className="card">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 flex items-center mb-4">
              <Apple className="h-6 w-6 text-warning-600 dark:text-warning-400 mr-2" />
              {t('clientPortal.dietPlan')} — Hoy
            </h2>
            {hasDiet ? (
              <div>
                <p className="text-gray-600 dark:text-gray-400 mb-1">
                  <span className="font-medium">{t('clientPortal.goal')}:</span> {diet_plan_active!.goal}
                </p>
                {diet_plan_active!.total_calories != null && (
                  <p className="text-gray-600 dark:text-gray-400 mb-3">
                    {t('clientPortal.dailyCalories')}: {diet_plan_active!.total_calories} {t('clientPortal.kcal')}
                  </p>
                )}
                {diet_plan_active!.meals?.length > 0 && (
                  <div className="space-y-4 mb-3">
                    {diet_plan_active!.meals.map((m, i) => (
                      <div key={i}>
                        <p className="font-medium text-gray-900 dark:text-gray-100 mb-1">
                          {m.title || m.meal_type}
                        </p>
                        {m.foods?.length > 0 ? (
                          <ul className="list-disc list-inside text-gray-700 dark:text-gray-300 space-y-0.5 ml-2">
                            {m.foods.map((f) => (
                              <li key={f.id}>
                                {f.name}
                                {f.quantity != null && f.unit
                                  ? ` — ${Number(f.quantity) === Math.floor(Number(f.quantity)) ? Math.floor(f.quantity) : f.quantity} ${f.unit}`
                                  : ''}
                                {f.calories != null ? ` (${f.calories} kcal)` : ''}
                              </li>
                            ))}
                          </ul>
                        ) : null}
                      </div>
                    ))}
                  </div>
                )}
                {diet_plan_active!.coach_message && (
                  <div className="flex items-start gap-2 p-3 bg-primary-50 dark:bg-primary-900/20 rounded-lg">
                    <MessageSquare className="h-5 w-5 text-primary-600 dark:text-primary-400 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-gray-700 dark:text-gray-300">{diet_plan_active!.coach_message}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <Apple className="h-12 w-12 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400">{t('clientPortal.noDietPlan')}</p>
                <p className="text-sm text-gray-400 dark:text-gray-500">{t('clientPortal.contactCoach')}</p>
              </div>
            )}
          </div>

          {/* Training card */}
          <div className="card">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 flex items-center mb-4">
              <Dumbbell className="h-6 w-6 text-danger-600 dark:text-danger-400 mr-2" />
              {t('clientPortal.workoutPlan')} — Hoy
            </h2>
            {hasTraining ? (
              <div>
                <p className="text-gray-600 dark:text-gray-400 mb-1">
                  <span className="font-medium">Tipo:</span> {training_plan_active!.recommendation_type}
                </p>
                {(training_plan_active!.training_group_label || training_plan_active!.training_group) && (
                  <p className="text-gray-600 dark:text-gray-400 mb-1">
                    <span className="font-medium">Grupo:</span>{' '}
                    {training_plan_active!.training_group_label || training_plan_active!.training_group}
                  </p>
                )}
                {training_plan_active!.reasoning_summary && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">{training_plan_active!.reasoning_summary}</p>
                )}
                {training_plan_active!.recommended_video ? (
                  <div className="flex items-center gap-2 p-3 bg-gray-100 dark:bg-gray-700 rounded-lg mb-3">
                    <Video className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                    <div>
                      <p className="font-medium text-gray-900 dark:text-gray-100">
                        {training_plan_active!.recommended_video.title}
                      </p>
                      {training_plan_active!.recommended_video.duration_minutes != null && (
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {training_plan_active!.recommended_video.duration_minutes} min
                        </p>
                      )}
                    </div>
                  </div>
                ) : (
                  training_plan_active!.exercises?.length > 0 && (
                    <ul className="space-y-2 mb-3">
                      {training_plan_active!.exercises
                        .sort((a, b) => a.order - b.order)
                        .map((ex, i) => (
                          <li key={i} className="flex justify-between text-gray-700 dark:text-gray-300">
                            <span>{ex.name}</span>
                            <span className="text-gray-500 dark:text-gray-400">
                              {ex.sets}×{ex.reps}
                            </span>
                          </li>
                        ))}
                    </ul>
                  )
                )}
                {training_plan_active!.coach_message && (
                  <div className="flex items-start gap-2 p-3 bg-primary-50 dark:bg-primary-900/20 rounded-lg">
                    <MessageSquare className="h-5 w-5 text-primary-600 dark:text-primary-400 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-gray-700 dark:text-gray-300">{training_plan_active!.coach_message}</p>
                  </div>
                )}
                <button
                  type="button"
                  onClick={() => navigate('/client/workout-session')}
                  className="mt-3 inline-flex items-center gap-2 px-4 py-2 rounded-md bg-primary-600 text-white hover:bg-primary-700"
                >
                  Registrar entrenamiento
                </button>
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

        {/* Empty state when no recommendations at all */}
        {emptyRecommendations && (
          <div className="mt-8 card text-center py-8">
            <p className="text-gray-500 dark:text-gray-400">
              No hay recomendaciones todavía. La dieta se actualiza cada 15 días y el entrenamiento cada día.
            </p>
          </div>
        )}
          </>
        )}
      </div>
    </div>
  )
}
