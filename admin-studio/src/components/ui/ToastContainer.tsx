import { useToastStore } from '@/store/toast.store'

export function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts)
  const remove = useToastStore((s) => s.remove)

  if (!toasts.length) return null

  return (
    <div className="toast-container" role="log" aria-live="polite" aria-label="Notifications">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`toast toast-${t.kind}`}
          role="alert"
        >
          <span style={{ flex: 1 }}>{t.message}</span>
          <button
            className="btn btn-ghost btn-sm btn-icon"
            onClick={() => remove(t.id)}
            aria-label="Dismiss"
            style={{ marginLeft: 'var(--space-2)', minHeight: 24 }}
          >
            ×
          </button>
        </div>
      ))}
    </div>
  )
}
