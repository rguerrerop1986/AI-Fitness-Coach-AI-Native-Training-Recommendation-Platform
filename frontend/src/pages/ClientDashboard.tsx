import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { 
  User, 
  Apple, 
  Dumbbell, 
  TrendingUp, 
  Download, 
  LogOut,
  Calendar,
  Scale,
  Target,
  Clock
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
  const [clientData, setClientData] = useState<ClientData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const { t } = useTranslation()

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
        // Token expired or invalid, redirect to login
        localStorage.removeItem('client_access_token')
        localStorage.removeItem('client_refresh_token')
        localStorage.removeItem('client_info')
        navigate('/client/login')
        return
      }
      setError('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('client_access_token')
    localStorage.removeItem('client_refresh_token')
    localStorage.removeItem('client_info')
    delete api.defaults.headers.common['Authorization']
    navigate('/client/login')
  }

  const downloadPlan = async (planType: 'diet' | 'workout', assignmentId: number) => {
    try {
      const endpoint = planType === 'diet' 
        ? `/client/plans/${assignmentId}/download_diet_pdf/`
        : `/client/plans/${assignmentId}/download_workout_pdf/`
      
      const response = await api.get(endpoint, {
        responseType: 'blob'
      })

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${planType}_plan.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Error downloading plan:', error)
      alert('Failed to download plan. Please try again.')
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
          Try Again
        </button>
      </div>
    )
  }

  if (!clientData) {
    return <div>No data available</div>
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <User className="h-8 w-8 text-primary-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Welcome, {clientData.first_name}!
                </h1>
                <p className="text-gray-600">Your personalized fitness dashboard</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/client/appointments')}
                className="flex items-center text-gray-600 hover:text-gray-900"
              >
                <Clock className="h-5 w-5 mr-2" />
                Appointments
              </button>
              <button
                onClick={handleLogout}
                className="flex items-center text-gray-600 hover:text-gray-900"
              >
                <LogOut className="h-5 w-5 mr-2" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Scale className="h-8 w-8 text-primary-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Current Weight
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {clientData.latest_measurement?.weight_kg || clientData.initial_weight_kg} kg
                  </dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Target className="h-8 w-8 text-success-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Height
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
                <Apple className="h-8 w-8 text-warning-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Active Diet Plan
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
                <Dumbbell className="h-8 w-8 text-danger-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Active Workout Plan
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
              <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                <Apple className="h-6 w-6 text-warning-600 mr-2" />
                Diet Plan
              </h2>
            </div>
            
            {clientData.active_diet_plan ? (
              <div>
                <div className="mb-4">
                  <h3 className="text-lg font-medium text-gray-900">
                    {clientData.active_diet_plan.title}
                  </h3>
                  <p className="text-gray-600">
                    Goal: {clientData.active_diet_plan.goal}
                  </p>
                  <p className="text-gray-600">
                    Daily Calories: {clientData.active_diet_plan.daily_calories} kcal
                  </p>
                  <p className="text-sm text-gray-500">
                    Assigned: {new Date(clientData.active_diet_plan.assigned_date).toLocaleDateString()}
                  </p>
                </div>
                
                <div className="flex space-x-3">
                  <button
                    onClick={() => downloadPlan('diet', 1)} // You'll need to get the actual assignment ID
                    className="flex items-center bg-warning-600 text-white px-4 py-2 rounded hover:bg-warning-700"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download PDF
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <Apple className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No diet plan assigned yet</p>
                <p className="text-sm text-gray-400">Contact your coach to get started</p>
              </div>
            )}
          </div>

          {/* Workout Plan */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                <Dumbbell className="h-6 w-6 text-danger-600 mr-2" />
                Workout Plan
              </h2>
            </div>
            
            {clientData.active_workout_plan ? (
              <div>
                <div className="mb-4">
                  <h3 className="text-lg font-medium text-gray-900">
                    {clientData.active_workout_plan.title}
                  </h3>
                  <p className="text-gray-600">
                    Goal: {clientData.active_workout_plan.goal}
                  </p>
                  <p className="text-sm text-gray-500">
                    Assigned: {new Date(clientData.active_workout_plan.assigned_date).toLocaleDateString()}
                  </p>
                </div>
                
                <div className="flex space-x-3">
                  <button
                    onClick={() => downloadPlan('workout', 1)} // You'll need to get the actual assignment ID
                    className="flex items-center bg-danger-600 text-white px-4 py-2 rounded hover:bg-danger-700"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download PDF
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <Dumbbell className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No workout plan assigned yet</p>
                <p className="text-sm text-gray-400">Contact your coach to get started</p>
              </div>
            )}
          </div>
        </div>

        {/* Measurements Section */}
        {clientData.latest_measurement && (
          <div className="mt-8">
            <div className="card">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <TrendingUp className="h-6 w-6 text-success-600 mr-2" />
                Latest Measurements
                <span className="text-sm font-normal text-gray-500 ml-2">
                  ({new Date(clientData.latest_measurement.date).toLocaleDateString()})
                </span>
              </h2>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-gray-50 rounded">
                  <div className="text-2xl font-bold text-gray-900">
                    {clientData.latest_measurement.weight_kg}
                  </div>
                  <div className="text-sm text-gray-500">Weight (kg)</div>
                </div>
                
                {clientData.latest_measurement.body_fat_pct && (
                  <div className="text-center p-4 bg-gray-50 rounded">
                    <div className="text-2xl font-bold text-gray-900">
                      {clientData.latest_measurement.body_fat_pct}%
                    </div>
                    <div className="text-sm text-gray-500">Body Fat</div>
                  </div>
                )}
                
                {clientData.latest_measurement.chest_cm && (
                  <div className="text-center p-4 bg-gray-50 rounded">
                    <div className="text-2xl font-bold text-gray-900">
                      {clientData.latest_measurement.chest_cm}
                    </div>
                    <div className="text-sm text-gray-500">Chest (cm)</div>
                  </div>
                )}
                
                {clientData.latest_measurement.waist_cm && (
                  <div className="text-center p-4 bg-gray-50 rounded">
                    <div className="text-2xl font-bold text-gray-900">
                      {clientData.latest_measurement.waist_cm}
                    </div>
                    <div className="text-sm text-gray-500">Waist (cm)</div>
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
