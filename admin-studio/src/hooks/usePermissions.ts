/**
 * usePermissions — reactive permission helper.
 * Use this for permission-conditional rendering.
 *
 * @example
 *   const { can } = usePermissions()
 *   if (can('users:write')) { ... }
 */
import { useAuthStore } from '@/store/auth.store'

export function usePermissions() {
  const user = useAuthStore((s) => s.user)
  const hasPermission = useAuthStore((s) => s.hasPermission)

  return {
    /**
     * Returns true if the current user has the given permission.
     * Superadmins always return true.
     */
    can: (permission: string): boolean => hasPermission(permission),

    /**
     * Returns true if the current user has ALL of the given permissions.
     */
    canAll: (...permissions: string[]): boolean =>
      permissions.every((p) => hasPermission(p)),

    /**
     * Returns true if the current user has ANY of the given permissions.
     */
    canAny: (...permissions: string[]): boolean =>
      permissions.some((p) => hasPermission(p)),

    /** Shortcut: true if user is a superadmin */
    isSuperAdmin: user?.is_superadmin ?? false,

    /** All permissions the current user has */
    permissions: user?.permissions ?? [],

    /** All roles the current user belongs to */
    roles: user?.roles ?? [],
  }
}
