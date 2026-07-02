import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type ThemePreference = 'light' | 'dark' | 'system'

interface ThemeState {
  preference: ThemePreference
  setPreference: (p: ThemePreference) => void
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      preference: 'system',
      setPreference: (preference) => {
        set({ preference })
        applyTheme(preference)
      },
    }),
    { name: 'aegis_theme' },
  ),
)

export function applyTheme(preference: ThemePreference) {
  const root = document.documentElement
  if (preference === 'system') {
    root.removeAttribute('data-theme')
  } else {
    root.setAttribute('data-theme', preference)
  }
}
