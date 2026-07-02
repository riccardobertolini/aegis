import { create } from 'zustand'
import { api, setGlobalToken } from '@/lib/api-client'

export interface UserMe {
  id: string
  username: string
  full_name: string
  roles: string[]
  permissions: string[]
  is_superadmin: boolean
}

interface AuthState {
  token: string | null
  user:  UserMe | null
  isLoading: boolean
  error: string | null
  login:  (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  fetchMe: () => Promise<void>
  hasPermission: (perm: string) => boolean
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  user:  null,
  isLoading: false,
  error: null,

  login: async (username, password) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.post<{ access_token: string; token_type: string }>(
        '/security/login',
        { username, password },
      )
      setGlobalToken(res.access_token)
      set({ token: res.access_token })
      await get().fetchMe()
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Login failed'
      set({ error: msg })
      throw e
    } finally {
      set({ isLoading: false })
    }
  },

  logout: async () => {
    try { await api.post('/security/logout') } catch {/* ignore */}
    setGlobalToken(null)
    set({ token: null, user: null })
  },

  fetchMe: async () => {
    try {
      const user = await api.get<UserMe>('/security/me')
      set({ user })
    } catch {
      setGlobalToken(null)
      set({ token: null, user: null })
    }
  },

  hasPermission: (perm) => {
    const { user } = get()
    if (!user) return false
    if (user.is_superadmin) return true
    return user.permissions.includes(perm)
  },
}))
