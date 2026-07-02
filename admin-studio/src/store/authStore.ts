import { create } from 'zustand'
import { setTokenGetter } from '../lib/api'

interface AuthState {
  token: string | null
  username: string | null
  login: (token: string, username: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  username: null,
  login: (token, username) => {
    set({ token, username })
    setTokenGetter(() => get().token)
  },
  logout: () => {
    set({ token: null, username: null })
    setTokenGetter(() => null)
  },
}))
