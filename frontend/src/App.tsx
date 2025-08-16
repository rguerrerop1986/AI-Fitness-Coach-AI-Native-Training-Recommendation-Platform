import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
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

function AppRoutes() {
  return (
    <Routes>
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
    </Routes>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}

export default App
