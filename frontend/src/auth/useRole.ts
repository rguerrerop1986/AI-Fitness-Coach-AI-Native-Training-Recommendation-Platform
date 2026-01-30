/**
 * Unified hook to get current user role from either auth context
 */
import { useContext } from 'react'
import { AuthContext } from '../contexts/AuthContext'
import { ClientAuthContext } from '../contexts/ClientAuthContext'
import { normalizeRole, UserRole } from './roles'

export interface UseRoleResult {
  role: UserRole | null
  isAuthenticated: boolean
  loading: boolean
  isClient: boolean
  isCoach: boolean
}

export function useRole(): UseRoleResult {
  // Use useContext directly to avoid throwing if context is not available
  const authContext = useContext(AuthContext)
  const clientAuthContext = useContext(ClientAuthContext)

  // If coach/admin is authenticated, use that role
  if (authContext?.user) {
    const rawRole = normalizeRole(authContext.user.role)
    const role: UserRole = rawRole ?? 'coach'
    return {
      role,
      isAuthenticated: true,
      loading: authContext.loading ?? false,
      isClient: role === 'client',
      isCoach: role === 'coach' || role === 'assistant',
    }
  }

  // If client is authenticated, return client role
  if (clientAuthContext?.client) {
    return {
      role: 'client',
      isAuthenticated: true,
      loading: clientAuthContext.loading ?? false,
      isClient: true,
      isCoach: false,
    }
  }

  // Not authenticated
  return {
    role: null,
    isAuthenticated: false,
    loading: (authContext?.loading ?? false) || (clientAuthContext?.loading ?? false),
    isClient: false,
    isCoach: false,
  }
}
