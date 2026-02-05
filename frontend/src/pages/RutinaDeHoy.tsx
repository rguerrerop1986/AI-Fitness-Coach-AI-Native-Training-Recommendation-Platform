/**
 * "Rutina de Hoy" – Client view for today's suggested workout.
 * Shows suggested exercise, rationale, and feedback form (DONE / NOT_DONE / SKIPPED + RPE, energy, pain, notes).
 */
import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTheme } from '../contexts/ThemeContext'
import { Dumbbell, ArrowLeft, Sun, Moon, LogOut, User, CheckCircle, XCircle, SkipForward } from 'lucide-react'
import { api } from '../lib/api'
import { toast } from 'react-hot-toast'

const EXECUTION_OPTIONS = [
  { value: 'done', label: 'Completé', Icon: CheckCircle },
  { value: 'not_done', label: 'No hice', Icon: XCircle },
  { value: 'skipped', label: 'Omití', Icon: SkipForward },
] as const

type ExecutionStatus = typeof EXECUTION_OPTIONS[number]['value']

interface ExerciseSummary {
  id: number
  name: string
  image_url?: string
}

interface TrainingLogData {
  id?: number
  date: string
  suggested_exercise: number | null
  suggested_exercise_summary: ExerciseSummary | null
  executed_exercise: number | null
  executed_exercise_summary: ExerciseSummary | null
  execution_status: string
  rpe: number | null
  energy_level: number | null
  pain_level: number | null
  notes: string
  recommendation_version?: string
  recommendation_meta?: Record<string, unknown>
  recommendation_confidence?: string
}

function todayISO(): string {
  return new Date().toISOString().slice(0, 10)
}

/** Extract rationale from notes (line starting with [Rutina]) */
function getRationaleFromNotes(notes: string): string {
  if (!notes) return ''
  const match = notes.match(/\[Rutina\]\s*(.+?)(?=\n|$)/s)
  return match ? match[1].trim() : ''
}

export default function RutinaDeHoy() {
  const navigate = useNavigate()
  const { theme, toggleTheme } = useTheme()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [log, setLog] = useState<TrainingLogData | null>(null)
  const date = todayISO()

  const [executionStatus, setExecutionStatus] = useState<ExecutionStatus>('not_done')
  const [rpe, setRpe] = useState<number | ''>(5)
  const [energyLevel, setEnergyLevel] = useState<number | ''>(5)
  const [painLevel, setPainLevel] = useState<number | ''>(0)
  const [notes, setNotes] = useState('')

  const fetchLog = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.get(`/client/me/training-log/?date=${date}`)
      const data = res.data?.data as TrainingLogData | null | undefined
      if (data) {
        setLog(data)
        setExecutionStatus((data.execution_status as ExecutionStatus) || 'not_done')
        setRpe(data.rpe ?? '')
        setEnergyLevel(data.energy_level ?? '')
        setPainLevel(data.pain_level ?? '')
        setNotes(data.notes?.replace(/\[Rutina\].*$/s, '').trim() ?? '')
      } else {
        setLog(null)
        setExecutionStatus('not_done')
        setRpe(5)
        setEnergyLevel(5)
        setPainLevel(0)
        setNotes('')
      }
    } catch (err: unknown) {
      const ax = err as { response?: { status?: number } }
      if (ax.response?.status === 401) {
        localStorage.removeItem('client_access_token')
        localStorage.removeItem('client_refresh_token')
        localStorage.removeItem('client_info')
        navigate('/')
        return
      }
      toast.error('Error al cargar la rutina')
    } finally {
      setLoading(false)
    }
  }, [date, navigate])

  useEffect(() => {
    fetchLog()
  }, [fetchLog])

  const handleSubmit = async () => {
    setSaving(true)
    try {
      const payload: Record<string, unknown> = {
        execution_status: executionStatus,
        notes: notes.trim(),
      }
      if (executionStatus !== 'not_done' && executionStatus !== 'skipped') {
        if (rpe !== '') payload.rpe = Number(rpe)
        if (energyLevel !== '') payload.energy_level = Number(energyLevel)
        if (painLevel !== '') payload.pain_level = Number(painLevel)
      }
      await api.post(`/client/me/training-log/?date=${date}`, payload)
      toast.success('Feedback guardado')
      fetchLog()
    } catch (e: unknown) {
      const ax = e as { response?: { data?: { detail?: string } } }
      toast.error(ax.response?.data?.detail || 'Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  const rationale = log?.notes ? getRationaleFromNotes(log.notes) : ''
  const suggested = log?.suggested_exercise_summary

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate('/client/dashboard')}
                className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 text-sm font-medium flex items-center gap-1"
              >
                <ArrowLeft className="h-4 w-4" /> Dashboard
              </button>
              <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                Rutina de hoy
              </h1>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={toggleTheme} className="p-2 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700">
                {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
              </button>
              <button onClick={() => navigate('/client/dashboard')} className="p-2 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700">
                <User className="h-5 w-5" />
              </button>
              <button
                onClick={() => {
                  localStorage.removeItem('client_access_token')
                  localStorage.removeItem('client_refresh_token')
                  localStorage.removeItem('client_info')
                  navigate('/')
                }}
                className="p-2 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600" />
          </div>
        ) : (
          <>
            {/* Suggested workout card */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                <Dumbbell className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                Ejercicio sugerido
              </h2>
              {suggested ? (
                <>
                  <p className="text-xl font-medium text-gray-900 dark:text-gray-100 mb-2">
                    {suggested.name}
                  </p>
                  {rationale && (
                    <p className="text-gray-600 dark:text-gray-400 text-sm mb-4 pl-0 border-l-0">
                      {rationale}
                    </p>
                  )}
                </>
              ) : (
                <p className="text-gray-500 dark:text-gray-400">
                  Aún no hay una rutina sugerida para hoy. Tu coach puede activarla o revisa más tarde.
                </p>
              )}
            </div>

            {/* Feedback */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                ¿Cómo fue tu entrenamiento?
              </h2>
              <div className="flex flex-wrap gap-2 mb-4">
                {EXECUTION_OPTIONS.map(({ value, label, Icon }) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => setExecutionStatus(value)}
                    className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium ${
                      executionStatus === value
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                    }`}
                  >
                    <Icon className="h-4 w-4" /> {label}
                  </button>
                ))}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Esfuerzo (RPE) {rpe !== '' && `· ${rpe}`}
                  </label>
                  <input
                    type="range"
                    min={1}
                    max={10}
                    value={rpe === '' ? 5 : rpe}
                    onChange={(e) => setRpe(Number(e.target.value))}
                    className="w-full h-2 rounded-lg appearance-none cursor-pointer bg-gray-200 dark:bg-gray-600 accent-primary-600"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Energía {energyLevel !== '' && `· ${energyLevel}`}
                  </label>
                  <input
                    type="range"
                    min={1}
                    max={10}
                    value={energyLevel === '' ? 5 : energyLevel}
                    onChange={(e) => setEnergyLevel(Number(e.target.value))}
                    className="w-full h-2 rounded-lg appearance-none cursor-pointer bg-gray-200 dark:bg-gray-600 accent-primary-600"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Dolor (0–10) {painLevel !== '' && `· ${painLevel}`}
                  </label>
                  <input
                    type="range"
                    min={0}
                    max={10}
                    value={painLevel === '' ? 0 : painLevel}
                    onChange={(e) => setPainLevel(Number(e.target.value))}
                    className="w-full h-2 rounded-lg appearance-none cursor-pointer bg-gray-200 dark:bg-gray-600 accent-primary-600"
                  />
                </div>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Notas (opcional)
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="¿Cómo te sentiste?"
                  rows={2}
                  className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm"
                />
              </div>

              <button
                type="button"
                onClick={handleSubmit}
                disabled={saving}
                className="inline-flex items-center px-6 py-3 rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? (
                  <>
                    <span className="animate-spin mr-2 inline-block h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                    Guardando...
                  </>
                ) : (
                  'Enviar feedback'
                )}
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
