import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTheme } from '../contexts/ThemeContext'
import { useClientAuth } from '../contexts/ClientAuthContext'
import { Dumbbell, Apple, Calendar, Moon, Sun, LogOut, User, ChevronRight } from 'lucide-react'
import { api } from '../lib/api'
import { formatLocalYYYYMMDD } from '../lib/date'
import { getScaleLabel, getMetricDefinition, type DailyLogMetricKey } from '../lib/dailyLogMetrics'
import { toast } from 'react-hot-toast'

const EXECUTION_STATUSES = [
  { value: 'done', label: 'Completé' },
  { value: 'partial', label: 'Parcial' },
  { value: 'not_done', label: 'No hice' },
  { value: 'replaced', label: 'Reemplacé' },
] as const

type ExecutionStatus = typeof EXECUTION_STATUSES[number]['value']

/** Scale input with helper text and "¿Qué es?" collapsible for Daily Log metrics */
function ScaleBlock({
  metricKey,
  value,
  min,
  max,
  defaultValueWhenEmpty,
  label,
  onChange,
}: {
  metricKey: DailyLogMetricKey
  value: number | ''
  min: number
  max: number
  /** Value shown on the slider when value is empty (e.g. 5 for RPE) */
  defaultValueWhenEmpty: number
  label: string
  onChange: (n: number) => void
}) {
  const displayValue = value === '' ? defaultValueWhenEmpty : value
  const helperText = getScaleLabel(metricKey, value)
  const definition = getMetricDefinition(metricKey)
  const id = `${metricKey}-helper`

  return (
    <div className="space-y-1 min-h-[5.5rem]">
      <label htmlFor={metricKey} className="block text-sm font-medium text-gray-700 dark:text-gray-300">
        {label} {value !== '' && `· ${value}`}
      </label>
      <input
        id={metricKey}
        type="range"
        min={min}
        max={max}
        value={displayValue}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-describedby={helperText ? id : undefined}
        className="w-full h-2 rounded-lg appearance-none cursor-pointer bg-gray-200 dark:bg-gray-600 accent-primary-600"
      />
      <div id={id} className="min-h-[1.25rem] text-xs text-gray-600 dark:text-gray-400" role="status">
        {helperText ?? '\u00A0'}
      </div>
      {definition && (
        <details className="group mt-1">
          <summary className="cursor-pointer list-none flex items-center gap-1 text-xs text-primary-600 dark:text-primary-400 font-medium">
            <ChevronRight className="h-3.5 w-3.5 group-open:rotate-90 transition-transform" />
            ¿Qué es?
          </summary>
          <div className="mt-1.5 pl-4 border-l-2 border-gray-200 dark:border-gray-600 space-y-1 text-xs text-gray-600 dark:text-gray-400">
            {definition.descriptionLines.map((line, i) => (
              <p key={i}>{line}</p>
            ))}
            <p className="font-medium mt-2 text-gray-700 dark:text-gray-300">Equivalencias:</p>
            <ul className="list-disc list-inside space-y-0.5">
              {definition.ranges.map((r) => (
                <li key={r.range}>
                  {r.range} → {r.label}
                </li>
              ))}
            </ul>
          </div>
        </details>
      )}
    </div>
  )
}

interface Exercise {
  id: number
  name: string
  muscle_group?: string
}

interface TrainingLogData {
  id?: number
  execution_status: string
  executed_exercise: number | null
  executed_exercise_summary?: { id: number; name: string; image_url: string } | null
  rpe: number | null
  energy_level: number | null
  pain_level: number | null
  notes: string
  duration_minutes?: number | null
}

interface DietLogData {
  id?: number
  adherence_percent: number
  hunger_level: number | null
  cravings_level: number | null
  digestion_quality: number | null
  notes: string
}

export default function DailyLog() {
  const navigate = useNavigate()
  const { theme, toggleTheme } = useTheme()
  const { logout } = useClientAuth()
  const [selectedDate, setSelectedDate] = useState(formatLocalYYYYMMDD())
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  // Training form state
  const [executionStatus, setExecutionStatus] = useState<ExecutionStatus>('not_done')
  const [executedExerciseId, setExecutedExerciseId] = useState<number | null>(null)
  const [executedExerciseName, setExecutedExerciseName] = useState('')
  const [rpe, setRpe] = useState<number | ''>(5)
  const [energyLevel, setEnergyLevel] = useState<number | ''>(5)
  const [painLevel, setPainLevel] = useState<number | ''>(0)
  const [trainingNotes, setTrainingNotes] = useState('')

  // Diet form state
  const [adherencePercent, setAdherencePercent] = useState(50)
  const [hungerLevel, setHungerLevel] = useState<number | ''>(5)
  const [cravingsLevel, setCravingsLevel] = useState<number | ''>(5)
  const [digestionQuality, setDigestionQuality] = useState<number | ''>(5)
  const [dietNotes, setDietNotes] = useState('')

  // Exercise search
  const [exerciseSearch, setExerciseSearch] = useState('')
  const [exerciseResults, setExerciseResults] = useState<Exercise[]>([])
  const [exerciseSearching, setExerciseSearching] = useState(false)
  const [showExerciseDropdown, setShowExerciseDropdown] = useState(false)

  const dateQuery = selectedDate

  const fetchLogs = useCallback(async () => {
    setLoading(true)
    try {
      const [trainingRes, dietRes] = await Promise.all([
        api.get(`/client/me/training-log/?date=${dateQuery}`),
        api.get(`/client/me/diet-log/?date=${dateQuery}`),
      ])

      const training = trainingRes.data?.data as TrainingLogData | null | undefined
      const diet = dietRes.data?.data as DietLogData | null | undefined

      if (training) {
        setExecutionStatus((training.execution_status as ExecutionStatus) || 'not_done')
        setExecutedExerciseId(training.executed_exercise ?? null)
        setExecutedExerciseName(training.executed_exercise_summary?.name ?? '')
        setRpe(training.rpe ?? '')
        setEnergyLevel(training.energy_level ?? '')
        setPainLevel(training.pain_level ?? '')
        setTrainingNotes(training.notes ?? '')
      } else {
        setExecutionStatus('not_done')
        setExecutedExerciseId(null)
        setExecutedExerciseName('')
        setRpe(5)
        setEnergyLevel(5)
        setPainLevel(0)
        setTrainingNotes('')
      }

      if (diet) {
        setAdherencePercent(diet.adherence_percent ?? 0)
        setHungerLevel(diet.hunger_level ?? '')
        setCravingsLevel(diet.cravings_level ?? '')
        setDigestionQuality(diet.digestion_quality ?? '')
        setDietNotes(diet.notes ?? '')
      } else {
        setAdherencePercent(50)
        setHungerLevel(5)
        setCravingsLevel(5)
        setDigestionQuality(5)
        setDietNotes('')
      }
    } catch (err: any) {
      if (err.response?.status === 401) {
        localStorage.removeItem('client_access_token')
        localStorage.removeItem('client_refresh_token')
        localStorage.removeItem('client_info')
        navigate('/')
        return
      }
      toast.error(err.response?.data?.error || 'Error al cargar el registro')
    } finally {
      setLoading(false)
    }
  }, [dateQuery, navigate])

  useEffect(() => {
    fetchLogs()
  }, [fetchLogs])

  const searchExercises = useCallback(async (q: string) => {
    if (!q.trim()) {
      setExerciseResults([])
      return
    }
    setExerciseSearching(true)
    try {
      const res = await api.get(`/exercises/?search=${encodeURIComponent(q)}`)
      const list = res.data?.results ?? res.data ?? []
      setExerciseResults(Array.isArray(list) ? list : [])
    } catch {
      setExerciseResults([])
    } finally {
      setExerciseSearching(false)
    }
  }, [])

  useEffect(() => {
    const t = setTimeout(() => searchExercises(exerciseSearch), 300)
    return () => clearTimeout(t)
  }, [exerciseSearch, searchExercises])

  const maxDate = formatLocalYYYYMMDD()

  const handleSave = async () => {
    setSaving(true)
    let trainingOk = false
    let dietOk = false

    try {
      const trainingPayload: Record<string, unknown> = {
        execution_status: executionStatus,
        notes: trainingNotes,
      }
      if (executionStatus !== 'not_done') {
        if (executedExerciseId) trainingPayload.executed_exercise = executedExerciseId
        if (rpe !== '') trainingPayload.rpe = Number(rpe)
        if (energyLevel !== '') trainingPayload.energy_level = Number(energyLevel)
        if (painLevel !== '') trainingPayload.pain_level = Number(painLevel)
      } else {
        trainingPayload.executed_exercise = null
      }

      try {
        await api.post(`/client/me/training-log/?date=${dateQuery}`, trainingPayload)
        trainingOk = true
        toast.success('Entrenamiento guardado')
      } catch (e: any) {
        toast.error(e.response?.data?.execution_status?.[0] || e.response?.data?.detail || 'Error al guardar entrenamiento')
      }

      const dietPayload = {
        adherence_percent: adherencePercent,
        hunger_level: hungerLevel === '' ? null : Number(hungerLevel),
        cravings_level: cravingsLevel === '' ? null : Number(cravingsLevel),
        digestion_quality: digestionQuality === '' ? null : Number(digestionQuality),
        notes: dietNotes,
      }

      try {
        await api.post(`/client/me/diet-log/?date=${dateQuery}`, dietPayload)
        dietOk = true
        toast.success('Alimentación guardada')
      } catch (e: any) {
        toast.error(e.response?.data?.adherence_percent?.[0] || e.response?.data?.detail || 'Error al guardar alimentación')
      }

      if (trainingOk || dietOk) fetchLogs()
    } finally {
      setSaving(false)
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/', { replace: true })
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate('/client/dashboard')}
                className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 text-sm font-medium"
              >
                ← Dashboard
              </button>
              <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                Registro diario
              </h1>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={toggleTheme}
                className="p-2 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
              </button>
              <button
                onClick={() => navigate('/client/dashboard')}
                className="p-2 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <User className="h-5 w-5" />
              </button>
              <button
                onClick={handleLogout}
                className="p-2 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Date picker */}
        <div className="mb-6 flex items-center gap-2">
          <Calendar className="h-5 w-5 text-gray-500 dark:text-gray-400" />
          <label htmlFor="daily-log-date" className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Fecha
          </label>
          <input
            id="daily-log-date"
            type="date"
            value={selectedDate}
            max={maxDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600" />
          </div>
        ) : (
          <>
            {/* Training card */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                <Dumbbell className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                Entrenamiento de hoy
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    ¿Cómo fue tu entrenamiento?
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {EXECUTION_STATUSES.map(({ value, label }) => (
                      <button
                        key={value}
                        type="button"
                        onClick={() => setExecutionStatus(value)}
                        className={`px-3 py-2 rounded-md text-sm font-medium ${
                          executionStatus === value
                            ? 'bg-primary-600 text-white'
                            : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                        }`}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>

                {(executionStatus === 'done' || executionStatus === 'partial' || executionStatus === 'replaced') && (
                  <div className="relative">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      ¿Qué ejercicio o video realizaste?
                    </label>
                    <input
                      type="text"
                      value={exerciseSearch || executedExerciseName}
                      onChange={(e) => {
                        setExerciseSearch(e.target.value)
                        setShowExerciseDropdown(true)
                        if (!e.target.value) setExecutedExerciseId(null)
                      }}
                      onFocus={() => setShowExerciseDropdown(true)}
                      onBlur={() => setTimeout(() => setShowExerciseDropdown(false), 200)}
                      placeholder="Buscar ejercicio..."
                      className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm"
                    />
                    {showExerciseDropdown && (exerciseSearch || exerciseResults.length > 0) && (
                      <ul className="absolute z-10 mt-1 w-full max-h-48 overflow-auto rounded-md border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 shadow-lg">
                        {exerciseSearching ? (
                          <li className="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">Buscando...</li>
                        ) : exerciseResults.length === 0 ? (
                          <li className="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">Sin resultados</li>
                        ) : (
                          exerciseResults.map((ex) => (
                            <li
                              key={ex.id}
                              onMouseDown={(e) => e.preventDefault()}
                              onClick={() => {
                                setExecutedExerciseId(ex.id)
                                setExecutedExerciseName(ex.name)
                                setExerciseSearch('')
                                setShowExerciseDropdown(false)
                              }}
                              className="px-3 py-2 text-sm text-gray-900 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
                            >
                              {ex.name}
                            </li>
                          ))
                        )}
                      </ul>
                    )}
                  </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <ScaleBlock
                    metricKey="rpe"
                    value={rpe}
                    min={1}
                    max={10}
                    defaultValueWhenEmpty={5}
                    label="Esfuerzo percibido (RPE)"
                    onChange={setRpe}
                  />
                  <ScaleBlock
                    metricKey="energy_level"
                    value={energyLevel}
                    min={1}
                    max={10}
                    defaultValueWhenEmpty={5}
                    label="Nivel de energía"
                    onChange={setEnergyLevel}
                  />
                  <ScaleBlock
                    metricKey="pain_level"
                    value={painLevel}
                    min={0}
                    max={10}
                    defaultValueWhenEmpty={0}
                    label="Dolor (0–10)"
                    onChange={setPainLevel}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    ¿Cómo te sentiste? (opcional)
                  </label>
                  <textarea
                    value={trainingNotes}
                    onChange={(e) => setTrainingNotes(e.target.value)}
                    placeholder="¿Cómo te sentiste?"
                    rows={2}
                    className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm"
                  />
                </div>
              </div>
            </div>

            {/* Diet card */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                <Apple className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                Alimentación de hoy
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    ¿Qué tanto seguiste tu plan de alimentación? · {adherencePercent}%
                  </label>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={adherencePercent}
                    onChange={(e) => setAdherencePercent(Number(e.target.value))}
                    className="w-full h-2 rounded-lg appearance-none cursor-pointer bg-gray-200 dark:bg-gray-600 accent-primary-600"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <ScaleBlock
                    metricKey="hunger_level"
                    value={hungerLevel}
                    min={1}
                    max={10}
                    defaultValueWhenEmpty={5}
                    label="Hambre"
                    onChange={setHungerLevel}
                  />
                  <ScaleBlock
                    metricKey="cravings_level"
                    value={cravingsLevel}
                    min={1}
                    max={10}
                    defaultValueWhenEmpty={5}
                    label="Antojos"
                    onChange={setCravingsLevel}
                  />
                  <ScaleBlock
                    metricKey="digestion_quality"
                    value={digestionQuality}
                    min={1}
                    max={10}
                    defaultValueWhenEmpty={5}
                    label="Digestión"
                    onChange={setDigestionQuality}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Comentarios (opcional)
                  </label>
                  <textarea
                    value={dietNotes}
                    onChange={(e) => setDietNotes(e.target.value)}
                    placeholder="Comentarios sobre tu alimentación"
                    rows={2}
                    className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm"
                  />
                </div>
              </div>
            </div>

            {/* Single save button */}
            <div className="flex justify-end">
              <button
                type="button"
                onClick={handleSave}
                disabled={saving}
                className="inline-flex items-center px-6 py-3 rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? (
                  <>
                    <span className="animate-spin mr-2 inline-block h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                    Guardando...
                  </>
                ) : (
                  'Guardar registro'
                )}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
