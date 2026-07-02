/**
 * useAuth — convenience hook wrapping auth.store.
 * Exposes current user, loading state, login/logout,
 * and a permission checker.
 */
import { useAuthStore } from '@/store/auth.store'

export function useAuth() {
  const token        = useAuthStore((s) => s.token)
  const user         = useAuthStore((s) => s.user)
  const isLoading    = useAuthStore((s) => s.isLoading)
  const error        = useAuthStore((s) => s.error)
  const login        = useAuthStore((s) => s.login)
  const logout       = useAuthStore((s) => s.logout)
  const hasPermission = useAuthStore((s) => s.hasPermission)

  return {
    /** JWT token — null if not authenticated */
    token,
    /** Current user profile with roles & permissions */
    user,
    /** True while login/fetchMe is in-flight */
    isLoading,
    /** Last auth error message */
    error,
    /** Authenticate with username + password */
    login,
    /** Invalidate session locally and on the backend */
    logout,
    /** True if the current user has the given permission string */
    hasPermission,
    /** True if the current user is authenticated */
    isAuthenticated: token !== null,
    /** True if the current user is a superadmin (bypasses all permission checks) */
    isSuperAdmin: user?.is_superadmin ?? false,
  }
}
