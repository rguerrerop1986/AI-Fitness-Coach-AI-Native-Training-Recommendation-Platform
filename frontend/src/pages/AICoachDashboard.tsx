/**
 * AI Coach Dashboard – Coach (Sandy) view: alerts, adherence trend, per-client logs and risk.
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertTriangle,
  TrendingDown,
  Activity,
  User,
  ChevronDown,
  ChevronRight,
  Dumbbell,
  Calendar,
} from 'lucide-react'
import { api } from '../lib/api'

interface TrainingLogItem {
  id: number
  date: string
  suggested_exercise_summary: { id: number; name: string } | null
  executed_exercise_summary: { id: number; name: string } | null
  execution_status: string
  rpe: number | null
  energy_level: number | null
  pain_level: number | null
  notes: string
}

interface ClientBlock {
  client_id: number
  client_name: string
  logs: TrainingLogItem[]
  risk_score: number
}

interface DashboardData {
  coach_id: number
  days: number
  high_pain_clients: { client_id: number; client_name: string; pain_level: number }[]
  not_done_streak_clients: { client_id: number; client_name: string }[]
  adherence_trend: { client_id: number; client_name: string; adherence_rate: number; logs_count: number }[]
  by_client: ClientBlock[]
}

const STATUS_LABEL: Record<string, string> = {
  done: 'Hecho',
  not_done: 'No hecho',
  skipped: 'Omitido',
  partial: 'Parcial',
  replaced: 'Reemplazado',
  injury_stop: 'Lesión',
  sick: 'Enfermo',
}

export default function AICoachDashboard() {
  const navigate = useNavigate()
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(7)
  const [expanded, setExpanded] = useState<Set<number>>(new Set())

  useEffect(() => {
    let cancelled = false
    async function fetchData() {
      try {
        const res = await api.get(`/tracking/coach-dashboard/?days=${days}`)
        if (!cancelled) setData(res.data)
      } catch (e) {
        if (!cancelled) setData(null)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    fetchData()
    return () => { cancelled = true }
  }, [days])

  const toggleClient = (clientId: number) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(clientId)) next.delete(clientId)
      else next.add(clientId)
      return next
    })
  }

  const today = new Date().toISOString().slice(0, 10)

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[40vh]">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600" />
      </div>
    )
  }

  if (!data) {
    return (
      <div className="p-6">
        <p className="text-red-600">Error al cargar el dashboard.</p>
        <button
          onClick={() => navigate('/dashboard')}
          className="mt-2 text-primary-600 hover:underline"
        >
          Volver al dashboard
        </button>
      </div>
    )
  }

  return (
    <div className="p-4 md:p-6 max-w-6xl mx-auto">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
          <Activity className="h-7 w-7 text-primary-600" />
          AI Coach Dashboard
        </h1>
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600 dark:text-gray-400">Últimos</label>
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-2 py-1 text-sm"
          >
            <option value={7}>7 días</option>
            <option value={14}>14 días</option>
          </select>
        </div>
      </div>

      {/* Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
          <div className="flex items-center gap-2 text-amber-800 dark:text-amber-200 font-medium mb-2">
            <AlertTriangle className="h-5 w-5" />
            Dolor alto (≥6)
          </div>
          <p className="text-2xl font-bold text-amber-900 dark:text-amber-100">
            {data.high_pain_clients.length}
          </p>
          <ul className="mt-2 text-sm text-amber-700 dark:text-amber-300">
            {data.high_pain_clients.slice(0, 3).map((c) => (
              <li key={c.client_id}>{c.client_name} (dolor {c.pain_level})</li>
            ))}
            {data.high_pain_clients.length > 3 && (
              <li>+{data.high_pain_clients.length - 3} más</li>
            )}
          </ul>
        </div>

        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-800 dark:text-red-200 font-medium mb-2">
            <TrendingDown className="h-5 w-5" />
            2+ días sin hacer
          </div>
          <p className="text-2xl font-bold text-red-900 dark:text-red-100">
            {data.not_done_streak_clients.length}
          </p>
          <ul className="mt-2 text-sm text-red-700 dark:text-red-300">
            {data.not_done_streak_clients.slice(0, 3).map((c) => (
              <li key={c.client_id}>{c.client_name}</li>
            ))}
            {data.not_done_streak_clients.length > 3 && (
              <li>+{data.not_done_streak_clients.length - 3} más</li>
            )}
          </ul>
        </div>

        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="flex items-center gap-2 text-gray-800 dark:text-gray-200 font-medium mb-2">
            <TrendingDown className="h-5 w-5" />
            Adherencia semanal
          </div>
          <div className="space-y-1 text-sm">
            {data.adherence_trend
              .sort((a, b) => a.adherence_rate - b.adherence_rate)
              .slice(0, 5)
              .map((a) => (
                <div key={a.client_id} className="flex justify-between">
                  <span className="text-gray-700 dark:text-gray-300 truncate max-w-[140px]">{a.client_name}</span>
                  <span className={a.adherence_rate >= 0.6 ? 'text-green-600' : a.adherence_rate >= 0.4 ? 'text-amber-600' : 'text-red-600'}>
                    {Math.round(a.adherence_rate * 100)}%
                  </span>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Per-client */}
      <div className="space-y-2">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Por cliente
        </h2>
        {data.by_client.map((block) => {
          const isOpen = expanded.has(block.client_id)
          const todayLog = block.logs.find((l) => l.date === today)
          const last7 = block.logs.slice(0, 7)
          const adherence = data.adherence_trend.find((a) => a.client_id === block.client_id)?.adherence_rate ?? 0
          return (
            <div
              key={block.client_id}
              className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
            >
              <button
                type="button"
                onClick={() => toggleClient(block.client_id)}
                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700/50"
              >
                {isOpen ? (
                  <ChevronDown className="h-5 w-5 text-gray-500" />
                ) : (
                  <ChevronRight className="h-5 w-5 text-gray-500" />
                )}
                <User className="h-5 w-5 text-gray-500" />
                <span className="font-medium text-gray-900 dark:text-gray-100">{block.client_name}</span>
                <span className="text-sm text-gray-500">
                  Adherencia {Math.round(adherence * 100)}%
                </span>
                <span
                  className={`ml-auto text-sm font-medium ${
                    block.risk_score >= 70 ? 'text-red-600' : block.risk_score >= 40 ? 'text-amber-600' : 'text-green-600'
                  }`}
                >
                  Riesgo {block.risk_score}
                </span>
              </button>
              {isOpen && (
                <div className="border-t border-gray-200 dark:border-gray-700 px-4 py-3 space-y-3">
                  {todayLog && (
                    <div className="flex items-start gap-2 text-sm">
                      <Dumbbell className="h-4 w-4 text-primary-600 mt-0.5" />
                      <div>
                        <span className="font-medium">Hoy:</span>{' '}
                        {todayLog.suggested_exercise_summary?.name ?? 'Sin sugerencia'}
                        {todayLog.notes && (
                          <p className="text-gray-600 dark:text-gray-400 mt-1">{todayLog.notes}</p>
                        )}
                        <span className="text-gray-500">
                          {STATUS_LABEL[todayLog.execution_status] ?? todayLog.execution_status}
                          {todayLog.rpe != null && ` · RPE ${todayLog.rpe}`}
                        </span>
                      </div>
                    </div>
                  )}
                  <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <Calendar className="h-4 w-4" />
                    Últimos 7 registros
                  </div>
                  <ul className="space-y-2">
                    {last7.map((log) => (
                      <li
                        key={log.id}
                        className="flex flex-wrap items-center gap-2 text-sm py-1 border-b border-gray-100 dark:border-gray-700 last:border-0"
                      >
                        <span className="text-gray-500 w-24">{log.date}</span>
                        <span>{log.suggested_exercise_summary?.name ?? '–'}</span>
                        <span className="text-gray-500">{STATUS_LABEL[log.execution_status] ?? log.execution_status}</span>
                        {log.pain_level != null && log.pain_level >= 6 && (
                          <span className="text-amber-600">Dolor {log.pain_level}</span>
                        )}
                        {log.notes && (
                          <span className="text-gray-500 truncate max-w-[200px]" title={log.notes}>
                            {log.notes}
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
