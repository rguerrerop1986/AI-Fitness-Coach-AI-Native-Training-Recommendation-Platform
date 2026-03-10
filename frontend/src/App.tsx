import { Routes, Route, Navigate, useLocation, Outlet } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { ClientAuthProvider, useClientAuth } from './contexts/ClientAuthContext'
import { ThemeProvider } from './contexts/ThemeContext'
import RequireRole from './auth/RequireRole'
import { useRole } from './auth/useRole'
import Login from './pages/Login'
import RoleSelectPage from './pages/RoleSelectPage'
import Dashboard from './pages/Dashboard'
import Clients from './pages/Clients'
import CreateClient from './pages/CreateClient'
import ClientDetail from './pages/ClientDetail'
import CreateCheckIn from './pages/CreateCheckIn'
import Foods from './pages/Foods'
import FoodForm from './pages/FoodForm'
import Exercises from './pages/Exercises'
import ExerciseForm from './pages/ExerciseForm'
import Plans from './pages/Plans'
import PlanBuilder from './pages/PlanBuilder'
import CheckIns from './pages/CheckIns'
import Appointments from './pages/Appointments'
import AICoachDashboard from './pages/AICoachDashboard'
import Layout from './components/Layout'
import ClientLogin from './pages/ClientLogin'
import ClientDashboard from './pages/ClientDashboard'
import ClientAppointments from './pages/ClientAppointments'
import ClientPlan from './pages/ClientPlan'
import DailyLog from './pages/DailyLog'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  const { role } = useRole()
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    )
  }
  
  if (!user) {
    return <Navigate to="/" replace />
  }

  // Defense in depth: only redirect if user is explicitly a client
  // (Missing/unknown role with coach token → allow access so admin/staff can enter)
  if (role === 'client') {
    return <Navigate to="/client/dashboard" replace />
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
    return <Navigate to="/" replace />
  }
  
  return <>{children}</>
}

/** Renders role select at "/" or protected layout + outlet for /dashboard, /clients, etc. */
function RootWrapper() {
  const location = useLocation()
  const isLanding = location.pathname === '/'
  if (isLanding) {
    return <Outlet />
  }
  return (
    <ProtectedRoute>
      <Layout />
    </ProtectedRoute>
  )
}

function AppRoutes() {
  return (
    <Routes>
      {/* Landing: role selector at "/" */}
      <Route path="/" element={<RootWrapper />}>
        <Route index element={<RoleSelectPage />} />
        <Route path="dashboard" element={<Dashboard />} />
        {/* Coach-only routes */}
        <Route path="clients" element={
          <RequireRole allowedRoles={['coach', 'assistant']}>
            <Clients />
          </RequireRole>
        } />
        <Route path="clients/create" element={
          <RequireRole allowedRoles={['coach', 'assistant']}>
            <CreateClient />
          </RequireRole>
        } />
        <Route path="clients/:id" element={
          <RequireRole allowedRoles={['coach', 'assistant']}>
            <ClientDetail />
          </RequireRole>
        } />
        <Route path="clients/:clientId/check-in" element={
          <RequireRole allowedRoles={['coach', 'assistant']}>
            <CreateCheckIn />
          </RequireRole>
        } />
        <Route path="foods" element={
          <RequireRole allowedRoles={['coach', 'assistant']}>
            <Foods />
          </RequireRole>
        } />
        <Route path="foods/new" element={
          <RequireRole allowedRoles={['coach', 'assistant']}>
            <FoodForm />
          </RequireRole>
        } />
        <Route path="foods/:id/edit" element={
          <RequireRole allowedRoles={['coach', 'assistant']}>
            <FoodForm />
          </RequireRole>
        } />
        <Route path="exercises" element={
          <RequireRole allowedRoles={['coach', 'assistant']}>
            <Exercises />
          </RequireRole>
        } />
        <Route path="exercises/new" element={
          <RequireRole allowedRoles={['coach', 'assistant']}>
            <ExerciseForm />
          </RequireRole>
        } />
        <Route path="exercises/:id/edit" element={
          <RequireRole allowedRoles={['coach', 'assistant']}>
            <ExerciseForm />
          </RequireRole>
        } />
        {/* Shared routes (coach and client can access) */}
        <Route path="plans" element={<Plans />} />
        <Route path="plans/new" element={
          <RequireRole allowedRoles={['coach', 'assistant']}>
            <PlanBuilder />
          </RequireRole>
        } />
        <Route path="plans/:cycleId/builder" element={
          <RequireRole allowedRoles={['coach', 'assistant']}>
            <PlanBuilder />
          </RequireRole>
        } />
        <Route path="checkins" element={<CheckIns />} />
        <Route path="appointments" element={<Appointments />} />
        <Route path="ai-coach-dashboard" element={
          <RequireRole allowedRoles={['coach', 'assistant']}>
            <AICoachDashboard />
          </RequireRole>
        } />
      </Route>

      {/* Coach login (standalone, backward compatible) */}
      <Route path="/login" element={<Login />} />

      {/* Client Portal Routes */}
      <Route path="/client/login" element={<ClientLogin />} />
      <Route path="/client/dashboard" element={
        <ClientProtectedRoute>
          <ClientDashboard />
        </ClientProtectedRoute>
      } />
      <Route path="/client/appointments" element={
        <ClientProtectedRoute>
          <ClientAppointments />
        </ClientProtectedRoute>
      } />
      <Route path="/client/plan" element={
        <ClientProtectedRoute>
          <ClientPlan />
        </ClientProtectedRoute>
      } />
      <Route path="/client/daily-log" element={
        <ClientProtectedRoute>
          <DailyLog />
        </ClientProtectedRoute>
      } />
      <Route path="/client/rutina-de-hoy" element={<Navigate to="/client/dashboard" replace />} />
    </Routes>
  )
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ClientAuthProvider>
          <AppRoutes />
        </ClientAuthProvider>
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App
