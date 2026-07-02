import { useLocation } from 'react-router-dom'
import { useUIStore } from '@/store/ui.store'
import { useAuthStore } from '@/store/auth.store'
import './Topbar.css'

const ROUTE_LABELS: Record<string, string> = {
  dashboard:  'Dashboard',
  assistants: 'Assistants',
  knowledge:  'Knowledge Base',
  plugins:    'Plugins',
  users:      'Users',
  roles:      'Roles & Permissions',
  models:     'Models',
  training:   'Training',
  workflows:  'Workflows',
  features:   'Feature Toggles',
  languages:  'Languages',
  backup:     'Backup & Restore',
  audit:      'Audit Log',
  monitoring: 'Monitoring',
  templates:  'Templates',
  settings:   'Settings',
}

function ThemeToggle() {
  const theme    = useUIStore((s) => s.theme)
  const setTheme = useUIStore((s) => s.setTheme)
  const next = theme === 'dark' ? 'light' : theme === 'light' ? 'system' : 'dark'
  const labels = { light: '☀', dark: '☾', system: '⊙' }
  return (
    <button
      className="topbar-btn"
      onClick={() => setTheme(next)}
      title={`Theme: ${theme} → ${next}`}
      aria-label={`Switch to ${next} theme`}
    >
      <span style={{ fontSize: 14 }}>{labels[theme]}</span>
    </button>
  )
}

export function Topbar() {
  const { pathname } = useLocation()
  const user = useAuthStore((s) => s.user)
  const segment = pathname.split('/').filter(Boolean)[0] ?? 'dashboard'
  const label = ROUTE_LABELS[segment] ?? segment

  return (
    <header className="topbar">
      <div className="topbar-left">
        <span className="topbar-route">{label}</span>
      </div>
      <div className="topbar-right">
        <ThemeToggle />
        {user && (
          <div className="topbar-user">
            <div className="topbar-avatar">
              {(user.username[0] ?? 'A').toUpperCase()}
            </div>
            <span className="topbar-username">{user.username}</span>
          </div>
        )}
      </div>
    </header>
  )
}
