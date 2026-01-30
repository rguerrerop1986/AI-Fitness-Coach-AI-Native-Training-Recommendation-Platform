import { Navigate } from 'react-router-dom'
import { useRole } from './useRole'
import { UserRole } from './roles'

interface RequireRoleProps {
  children: React.ReactNode
  allowedRoles: UserRole[]
  redirectTo?: string
}

/**
 * Route guard component that restricts access based on user role
 * - If not authenticated, redirects to login
 * - If role not allowed, redirects to safe page (client dashboard or coach dashboard)
 */
export default function RequireRole({ children, allowedRoles, redirectTo }: RequireRoleProps) {
  const { role, isAuthenticated, loading } = useRole()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    // Determine login page based on attempted route
    const loginPath = redirectTo?.includes('/client') ? '/client/login' : '/login'
    return <Navigate to={loginPath} replace />
  }

  if (!role || !allowedRoles.includes(role)) {
    // Redirect to appropriate dashboard based on role
    if (role === 'client') {
      return <Navigate to="/client/dashboard" replace />
    }
    // Coach/admin should go to coach dashboard
    return <Navigate to="/dashboard" replace />
  }

  return <>{children}</>
}
