/**
 * Role-based access control helpers
 */

export type UserRole = 'client' | 'coach' | 'assistant'

/**
 * Normalize role to lowercase for consistent comparison.
 * Treats admin/administrator/staff as coach so they can access coach routes.
 */
export function normalizeRole(role: string | undefined | null): UserRole | null {
  if (!role) return null
  const normalized = role.toLowerCase().trim()
  if (['client', 'coach', 'assistant'].includes(normalized)) {
    return normalized as UserRole
  }
  // Django superuser / staff / "administrator" -> treat as coach
  if (['admin', 'administrator', 'staff', 'superuser'].includes(normalized)) {
    return 'coach'
  }
  return null
}

/**
 * Check if role is client
 */
export function isClient(role: string | undefined | null): boolean {
  return normalizeRole(role) === 'client'
}

/**
 * Check if role is coach or assistant
 */
export function isCoach(role: string | undefined | null): boolean {
  const normalized = normalizeRole(role)
  return normalized === 'coach' || normalized === 'assistant'
}

/**
 * Check if role is in allowed roles list
 */
export function hasRole(role: string | undefined | null, allowedRoles: UserRole[]): boolean {
  const normalized = normalizeRole(role)
  if (!normalized) return false
  return allowedRoles.includes(normalized)
}
