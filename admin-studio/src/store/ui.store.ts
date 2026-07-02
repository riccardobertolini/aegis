import { create } from 'zustand'

type Theme = 'light' | 'dark' | 'system'

interface UIState {
  sidebarCollapsed: boolean
  theme: Theme
  toggleSidebar:  () => void
  setSidebar:     (v: boolean) => void
  setTheme:       (t: Theme) => void
  applyTheme:     () => void
}

export const useUIStore = create<UIState>((set, get) => ({
  sidebarCollapsed: false,
  theme: 'system',

  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setSidebar:    (v) => set({ sidebarCollapsed: v }),

  setTheme: (t) => {
    set({ theme: t })
    get().applyTheme()
  },

  applyTheme: () => {
    const { theme } = get()
    const root = document.documentElement
    if (theme === 'system') {
      root.removeAttribute('data-theme')
    } else {
      root.setAttribute('data-theme', theme)
    }
  },
}))
