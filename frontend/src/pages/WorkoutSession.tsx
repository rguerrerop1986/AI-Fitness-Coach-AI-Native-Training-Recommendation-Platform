import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Dumbbell, Plus, Copy, Trash2, ArrowLeft, CheckCircle2, Video } from 'lucide-react'
import { toast } from 'react-hot-toast'

import { api } from '../lib/api'

type WorkoutType = 'video_workout' | 'gym_workout'
type SessionStatus = 'in_progress' | 'completed'

interface ExerciseSet {
  id: number
  set_number: number
  reps: number | null
  weight_kg: string | null
  intensity: number | null
  rest_seconds: number | null
}

interface WorkoutExercise {
  id: number
  exercise_name: string
  order: number
  notes: string
  intensity: number | null
  sets: ExerciseSet[]
}

interface WorkoutSession {
  id: number
  session_date: string
  workout_type: WorkoutType
  status: SessionStatus
  title: string
  video_name: string
  notes: string
  ai_summary: string
  completed_at: string | null
  total_exercises: number
  total_sets: number
  total_reps: number
  total_volume: string
  exercises: WorkoutExercise[]
}

interface AIPayloadResponse {
  totals: {
    total_exercises: number
    total_sets: number
    total_reps: number
    total_volume: number
  }
}

const today = new Date().toISOString().slice(0, 10)

export default function WorkoutSessionPage() {
  const navigate = useNavigate()

  const [workoutType, setWorkoutType] = useState<WorkoutType>('video_workout')
  const [title, setTitle] = useState('')
  const [videoName, setVideoName] = useState('')
  const [notes, setNotes] = useState('')
  const [aiSummary, setAiSummary] = useState('')

  const [session, setSession] = useState<WorkoutSession | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [completing, setCompleting] = useState(false)
  const [error, setError] = useState('')

  const isCompleted = session?.status === 'completed'

  const refreshSession = async (sessionId: number) => {
    const response = await api.get<WorkoutSession>(`/training/workout-sessions/${sessionId}/`)
    setSession(response.data)
  }

  const createSession = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await api.post<WorkoutSession>('/training/workout-sessions/', {
        session_date: today,
        workout_type: workoutType,
        title: title.trim(),
        video_name: videoName.trim(),
        notes: notes.trim(),
        ai_summary: aiSummary.trim(),
      })
      setSession(response.data)
      toast.success('Sesion iniciada')
    } catch (e: any) {
      const detail = e?.response?.data?.detail || 'No se pudo crear la sesion'
      setError(detail)
      toast.error(detail)
    } finally {
      setLoading(false)
    }
  }

  const updateSession = async (payload: Record<string, unknown>) => {
    if (!session) return
    setSaving(true)
    setError('')
    try {
      await api.patch(`/training/workout-sessions/${session.id}/`, payload)
      await refreshSession(session.id)
    } catch (e: any) {
      const detail = e?.response?.data?.detail || 'No se pudo actualizar la sesion'
      setError(detail)
      toast.error(detail)
    } finally {
      setSaving(false)
    }
  }

  const addExercise = async () => {
    if (!session) return
    const name = window.prompt('Nombre del ejercicio')
    if (!name) return
    setLoading(true)
    try {
      await api.post(`/training/workout-sessions/${session.id}/exercises/`, { exercise_name: name.trim() })
      await refreshSession(session.id)
    } catch {
      toast.error('No se pudo agregar el ejercicio')
    } finally {
      setLoading(false)
    }
  }

  const deleteExercise = async (exerciseId: number) => {
    if (!session) return
    setLoading(true)
    try {
      await api.delete(`/training/workout-sessions/${session.id}/exercises/${exerciseId}/`)
      await refreshSession(session.id)
    } catch {
      toast.error('No se pudo eliminar el ejercicio')
    } finally {
      setLoading(false)
    }
  }

  const addSet = async (exerciseId: number) => {
    if (!session) return
    setLoading(true)
    try {
      await api.post(`/training/workout-sessions/${session.id}/exercises/${exerciseId}/sets/`, {})
      await refreshSession(session.id)
    } catch {
      toast.error('No se pudo agregar el set')
    } finally {
      setLoading(false)
    }
  }

  const duplicateLastSet = async (exercise: WorkoutExercise) => {
    if (!session) return
    const sortedSets = [...exercise.sets].sort((a, b) => a.set_number - b.set_number)
    const lastSet = sortedSets[sortedSets.length - 1]
    if (!lastSet) {
      toast.error('No hay set para duplicar')
      return
    }
    setLoading(true)
    try {
      await api.post(`/training/workout-sessions/${session.id}/exercises/${exercise.id}/sets/`, {
        reps: lastSet.reps,
        weight_kg: lastSet.weight_kg,
        intensity: lastSet.intensity,
        rest_seconds: lastSet.rest_seconds,
      })
      await refreshSession(session.id)
    } catch {
      toast.error('No se pudo duplicar el set')
    } finally {
      setLoading(false)
    }
  }

  const updateSet = async (
    exerciseId: number,
    setId: number,
    field: 'reps' | 'weight_kg' | 'intensity' | 'rest_seconds',
    value: string
  ) => {
    if (!session) return
    const parsedValue: number | string | null =
      value === '' ? null : field === 'weight_kg' ? value : Number(value)
    try {
      await api.patch(`/training/workout-sessions/${session.id}/exercises/${exerciseId}/sets/${setId}/`, {
        [field]: parsedValue,
      })
      await refreshSession(session.id)
    } catch {
      toast.error('No se pudo actualizar el set')
    }
  }

  const deleteSet = async (exerciseId: number, setId: number) => {
    if (!session) return
    setLoading(true)
    try {
      await api.delete(`/training/workout-sessions/${session.id}/exercises/${exerciseId}/sets/${setId}/`)
      await refreshSession(session.id)
    } catch {
      toast.error('No se pudo eliminar el set')
    } finally {
      setLoading(false)
    }
  }

  const completeSession = async () => {
    if (!session) return
    setCompleting(true)
    setError('')
    try {
      await api.post(`/training/workout-sessions/${session.id}/complete/`)
      await refreshSession(session.id)
      toast.success('Sesion completada')
    } catch (e: any) {
      const detail = e?.response?.data?.detail || 'No se pudo completar la sesion'
      setError(detail)
      toast.error(detail)
    } finally {
      setCompleting(false)
    }
  }

  const technicalSummary = useMemo(() => {
    if (!session || session.status !== 'completed') return null
    return `${session.total_exercises} ejercicios, ${session.total_sets} sets, ${session.total_reps} reps, volumen ${session.total_volume} kg`
  }, [session])

  const fetchAiSummary = async () => {
    if (!session) return
    setLoading(true)
    try {
      const { data } = await api.get<AIPayloadResponse>(`/training/workout-sessions/${session.id}/ai-payload/`)
      setAiSummary(
        `Resumen tecnico: ejercicios=${data.totals.total_exercises}, sets=${data.totals.total_sets}, reps=${data.totals.total_reps}, volumen=${data.totals.total_volume}`
      )
    } catch {
      toast.error('No se pudo construir el payload de IA')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-5xl mx-auto py-8 px-4">
        <button
          type="button"
          onClick={() => navigate('/client/dashboard')}
          className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300 mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          Volver al dashboard
        </button>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Entrenamiento hibrido</h1>
          {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

          {!session && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm mb-1 text-gray-700 dark:text-gray-300">Tipo de entrenamiento</label>
                <select
                  value={workoutType}
                  onChange={(e) => setWorkoutType(e.target.value as WorkoutType)}
                  className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
                >
                  <option value="video_workout">Video workout</option>
                  <option value="gym_workout">Gym workout</option>
                </select>
              </div>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Titulo opcional de la sesion"
                className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
              />
              {workoutType === 'video_workout' && (
                <input
                  value={videoName}
                  onChange={(e) => setVideoName(e.target.value)}
                  placeholder="Nombre del video (ej. Insanity Max 30)"
                  className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
                />
              )}
              <textarea
                rows={2}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Notas opcionales"
                className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
              />
              <button
                type="button"
                onClick={createSession}
                disabled={loading}
                className="px-4 py-2 rounded-md bg-primary-600 text-white disabled:opacity-50"
              >
                {loading ? 'Creando...' : 'Iniciar sesion'}
              </button>
            </div>
          )}

          {session && (
            <div className="space-y-5">
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Tipo: <span className="font-medium">{session.workout_type}</span> · Estado:{' '}
                  <span className="font-medium">{session.status}</span>
                </p>
                {session.status === 'completed' && (
                  <span className="inline-flex items-center gap-1 text-sm text-green-700 dark:text-green-400">
                    <CheckCircle2 className="h-4 w-4" />
                    Finalizado
                  </span>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <input
                  value={session.title ?? ''}
                  onChange={(e) => {
                    setSession((prev) => (prev ? { ...prev, title: e.target.value } : prev))
                    void updateSession({ title: e.target.value })
                  }}
                  disabled={isCompleted || saving}
                  placeholder="Titulo de sesion"
                  className="rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 disabled:opacity-60"
                />
                {session.workout_type === 'video_workout' && (
                  <div className="flex items-center gap-2">
                    <Video className="h-4 w-4 text-primary-600" />
                    <input
                      value={session.video_name ?? ''}
                      onChange={(e) => {
                        setSession((prev) => (prev ? { ...prev, video_name: e.target.value } : prev))
                        void updateSession({ video_name: e.target.value })
                      }}
                      disabled={isCompleted || saving}
                      placeholder="Nombre del video"
                      className="flex-1 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 disabled:opacity-60"
                    />
                  </div>
                )}
              </div>

              <textarea
                rows={2}
                value={session.notes}
                onChange={(e) => {
                  setSession((prev) => (prev ? { ...prev, notes: e.target.value } : prev))
                  void updateSession({ notes: e.target.value })
                }}
                disabled={isCompleted || saving}
                placeholder="Notas de la sesion"
                className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 disabled:opacity-60"
              />

              {session.workout_type === 'gym_workout' && (
                <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-3">
                    <h2 className="font-medium flex items-center gap-2">
                      <Dumbbell className="h-4 w-4" />
                      Builder de gym
                    </h2>
                    <button
                      type="button"
                      onClick={addExercise}
                      disabled={isCompleted || loading}
                      className="inline-flex items-center gap-1 px-3 py-1.5 text-sm rounded-md bg-primary-600 text-white disabled:opacity-50"
                    >
                      <Plus className="h-4 w-4" />
                      Agregar ejercicio
                    </button>
                  </div>

                  {session.exercises.length === 0 && (
                    <p className="text-sm text-gray-500 dark:text-gray-400">Aun no agregas ejercicios.</p>
                  )}

                  <div className="space-y-4">
                    {session.exercises.map((exercise) => (
                      <div key={exercise.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                        <div className="flex justify-between items-start gap-2 mb-2">
                          <div className="flex-1">
                            <input
                              value={exercise.exercise_name}
                              disabled={isCompleted}
                              onChange={async (e) => {
                                const value = e.target.value
                                setSession((prev) =>
                                  prev
                                    ? {
                                        ...prev,
                                        exercises: prev.exercises.map((ex) =>
                                          ex.id === exercise.id ? { ...ex, exercise_name: value } : ex
                                        ),
                                      }
                                    : prev
                                )
                                await api.patch(`/training/workout-sessions/${session.id}/exercises/${exercise.id}/`, {
                                  exercise_name: value,
                                })
                              }}
                              className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-2 py-1.5 disabled:opacity-60"
                            />
                          </div>
                          <button
                            type="button"
                            onClick={() => deleteExercise(exercise.id)}
                            disabled={isCompleted}
                            className="text-red-600 disabled:opacity-50"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>

                        <div className="flex items-center gap-2 mb-2">
                          <button
                            type="button"
                            onClick={() => addSet(exercise.id)}
                            disabled={isCompleted || loading}
                            className="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-700"
                          >
                            + Set
                          </button>
                          <button
                            type="button"
                            onClick={() => duplicateLastSet(exercise)}
                            disabled={isCompleted || loading}
                            className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-700"
                          >
                            <Copy className="h-3 w-3" />
                            Duplicar ultimo set
                          </button>
                        </div>

                        <div className="space-y-2">
                          {[...exercise.sets]
                            .sort((a, b) => a.set_number - b.set_number)
                            .map((item) => (
                              <div key={item.id} className="grid grid-cols-12 gap-2 items-center">
                                <span className="col-span-2 text-xs text-gray-600 dark:text-gray-300">
                                  Set {item.set_number}
                                </span>
                                <input
                                  type="number"
                                  min={0}
                                  defaultValue={item.reps ?? ''}
                                  disabled={isCompleted}
                                  onBlur={(e) => void updateSet(exercise.id, item.id, 'reps', e.target.value)}
                                  placeholder="Reps"
                                  className="col-span-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-2 py-1 text-sm"
                                />
                                <input
                                  type="number"
                                  min={0}
                                  step="0.5"
                                  defaultValue={item.weight_kg ?? ''}
                                  disabled={isCompleted}
                                  onBlur={(e) => void updateSet(exercise.id, item.id, 'weight_kg', e.target.value)}
                                  placeholder="Peso"
                                  className="col-span-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-2 py-1 text-sm"
                                />
                                <input
                                  type="number"
                                  min={1}
                                  max={10}
                                  defaultValue={item.intensity ?? ''}
                                  disabled={isCompleted}
                                  onBlur={(e) => void updateSet(exercise.id, item.id, 'intensity', e.target.value)}
                                  placeholder="RPE"
                                  className="col-span-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-2 py-1 text-sm"
                                />
                                <input
                                  type="number"
                                  min={0}
                                  defaultValue={item.rest_seconds ?? ''}
                                  disabled={isCompleted}
                                  onBlur={(e) => void updateSet(exercise.id, item.id, 'rest_seconds', e.target.value)}
                                  placeholder="Descanso"
                                  className="col-span-3 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-2 py-1 text-sm"
                                />
                                <button
                                  type="button"
                                  onClick={() => deleteSet(exercise.id, item.id)}
                                  disabled={isCompleted}
                                  className="col-span-1 text-red-600 disabled:opacity-50"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </button>
                              </div>
                            ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <label className="block text-sm mb-1 text-gray-700 dark:text-gray-300">AI Summary</label>
                <textarea
                  rows={2}
                  value={aiSummary || session.ai_summary || ''}
                  onChange={(e) => setAiSummary(e.target.value)}
                  disabled={isCompleted}
                  className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 disabled:opacity-60"
                />
                <button
                  type="button"
                  onClick={fetchAiSummary}
                  disabled={loading}
                  className="mt-2 text-sm px-3 py-1.5 rounded bg-gray-100 dark:bg-gray-700"
                >
                  Construir payload resumido IA
                </button>
              </div>

              {!isCompleted && (
                <button
                  type="button"
                  onClick={completeSession}
                  disabled={completing}
                  className="px-5 py-2 rounded-md bg-green-600 text-white disabled:opacity-50"
                >
                  {completing ? 'Completando...' : 'Ya termine'}
                </button>
              )}

              {technicalSummary && (
                <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-md text-sm text-green-800 dark:text-green-300">
                  {technicalSummary}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
