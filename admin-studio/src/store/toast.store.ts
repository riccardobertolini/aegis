import { create } from 'zustand'

export type ToastKind = 'success' | 'error' | 'warning' | 'info'

export interface Toast {
  id: string
  kind: ToastKind
  message: string
  duration?: number
}

interface ToastState {
  toasts: Toast[]
  add:    (kind: ToastKind, message: string, duration?: number) => void
  remove: (id: string) => void
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  add: (kind, message, duration = 4000) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`
    set((s) => ({ toasts: [...s.toasts, { id, kind, message, duration }] }))
    if (duration > 0) {
      setTimeout(() => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })), duration)
    }
  },
  remove: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}))

// Convenience hook
export const useToast = () => {
  const { add } = useToastStore()
  return {
    success: (msg: string) => add('success', msg),
    error:   (msg: string) => add('error', msg),
    warning: (msg: string) => add('warning', msg),
    info:    (msg: string) => add('info', msg),
  }
}
