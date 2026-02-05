import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Users, Apple, Dumbbell, TrendingUp, Calendar, AlertTriangle } from 'lucide-react'

interface DashboardStats {
  total_clients: number
  active_clients: number
  total_foods: number
  total_exercises: number
  pending_checkins: number
  low_adherence_clients: number
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const { t } = useTranslation()

  useEffect(() => {
    const fetchStats = async () => {
      try {
        // For now, we'll simulate stats since we haven't implemented the backend endpoints yet
        setStats({
          total_clients: 2,
          active_clients: 2,
          total_foods: 10,
          total_exercises: 10,
          pending_checkins: 0,
          low_adherence_clients: 0,
        })
      } catch (error) {
        console.error('Error fetching dashboard stats:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{t('dashboard.title')}</h1>
        <p className="text-gray-600">{t('dashboard.subtitle')}</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Users className="h-8 w-8 text-primary-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  {t('dashboard.totalClients')}
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {stats?.total_clients}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <TrendingUp className="h-8 w-8 text-success-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  {t('dashboard.activeClients')}
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {stats?.active_clients}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Apple className="h-8 w-8 text-warning-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  {t('dashboard.totalFoods')}
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {stats?.total_foods}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Dumbbell className="h-8 w-8 text-danger-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Exercises in Catalog
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {stats?.total_exercises}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Calendar className="h-8 w-8 text-primary-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  {t('dashboard.pendingCheckIns')}
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {stats?.pending_checkins}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <AlertTriangle className="h-8 w-8 text-warning-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  {t('dashboard.lowAdherence')}
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {stats?.low_adherence_clients}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">{t('dashboard.quickActions')}</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Link
            to="/clients"
            className="flex items-center p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <Users className="h-6 w-6 text-primary-600 mr-3" />
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{t('dashboard.manageClients')}</span>
          </Link>
          
          <Link
            to="/foods"
            className="flex items-center p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <Apple className="h-6 w-6 text-warning-600 mr-3" />
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{t('dashboard.foodCatalog')}</span>
          </Link>
          
          <Link
            to="/exercises"
            className="flex items-center p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <Dumbbell className="h-6 w-6 text-danger-600 mr-3" />
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{t('dashboard.exerciseCatalog')}</span>
          </Link>
          
          <Link
            to="/plans"
            className="flex items-center p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <Calendar className="h-6 w-6 text-primary-600 mr-3" />
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{t('dashboard.createPlans')}</span>
          </Link>
          
          <Link
            to="/checkins"
            className="flex items-center p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <TrendingUp className="h-6 w-6 text-success-600 mr-3" />
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{t('dashboard.viewCheckins')}</span>
          </Link>
        </div>
      </div>
    </div>
  )
}
