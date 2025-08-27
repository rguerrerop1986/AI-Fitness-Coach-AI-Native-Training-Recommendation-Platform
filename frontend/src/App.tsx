import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { ClientAuthProvider, useClientAuth } from './contexts/ClientAuthContext'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Clients from './pages/Clients'
import CreateClient from './pages/CreateClient'
import ClientDetail from './pages/ClientDetail'
import CreateCheckIn from './pages/CreateCheckIn'
import Foods from './pages/Foods'
import Exercises from './pages/Exercises'
import Plans from './pages/Plans'
import CheckIns from './pages/CheckIns'
import Layout from './components/Layout'
import ClientLogin from './pages/ClientLogin'
import ClientDashboard from './pages/ClientDashboard'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    )
  }
  
  if (!user) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

function ClientProtectedRoute({ children }: { children: React.ReactNode }) {
  const { client, loading } = useClientAuth()
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    )
  }
  
  if (!client) {
    return <Navigate to="/client/login" replace />
  }
  
  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      {/* Coach/Admin Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/" element={
        <ProtectedRoute>
          <Layout />
        </ProtectedRoute>
      }>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="clients" element={<Clients />} />
        <Route path="clients/create" element={<CreateClient />} />
        <Route path="clients/:id" element={<ClientDetail />} />
        <Route path="clients/:clientId/check-in" element={<CreateCheckIn />} />
        <Route path="foods" element={<Foods />} />
        <Route path="exercises" element={<Exercises />} />
        <Route path="plans" element={<Plans />} />
        <Route path="checkins" element={<CheckIns />} />
      </Route>

      {/* Client Portal Routes */}
      <Route path="/client/login" element={<ClientLogin />} />
      <Route path="/client/dashboard" element={
        <ClientProtectedRoute>
          <ClientDashboard />
        </ClientProtectedRoute>
      } />
    </Routes>
  )
}

function App() {
  return (
    <AuthProvider>
      <ClientAuthProvider>
        <AppRoutes />
      </ClientAuthProvider>
    </AuthProvider>
  )
}

export default App
