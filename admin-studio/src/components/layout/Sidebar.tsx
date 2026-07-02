import { NavLink } from 'react-router-dom'
import { useUIStore } from '@/store/ui.store'
import { useAuthStore } from '@/store/auth.store'
import './Sidebar.css'

const NAV_ITEMS = [
  { label: 'Dashboard',      path: '/dashboard',  icon: 'dashboard' },
  { label: 'Assistants',     path: '/assistants', icon: 'bot' },
  { label: 'Knowledge',      path: '/knowledge',  icon: 'library' },
  { label: 'Plugins',        path: '/plugins',    icon: 'puzzle' },
  { label: 'Workflows',      path: '/workflows',  icon: 'workflow' },
  { label: 'Templates',      path: '/templates',  icon: 'template' },
]
const NAV_ADMIN = [
  { label: 'Users',          path: '/users',      icon: 'users' },
  { label: 'Roles',          path: '/roles',      icon: 'shield' },
  { label: 'Models',         path: '/models',     icon: 'model' },
  { label: 'Training',       path: '/training',   icon: 'training' },
  { label: 'Features',       path: '/features',   icon: 'toggle' },
  { label: 'Languages',      path: '/languages',  icon: 'language' },
]
const NAV_OPS = [
  { label: 'Monitoring',     path: '/monitoring', icon: 'chart' },
  { label: 'Audit Log',      path: '/audit',      icon: 'audit' },
  { label: 'Backup',         path: '/backup',     icon: 'backup' },
  { label: 'Settings',       path: '/settings',   icon: 'settings' },
]

const ICONS: Record<string, string> = {
  dashboard: 'M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z M9 22V12h6v10',
  bot:       'M12 2a2 2 0 0 1 2 2v1h1a3 3 0 0 1 3 3v8a3 3 0 0 1-3 3H9a3 3 0 0 1-3-3V8a3 3 0 0 1 3-3h1V4a2 2 0 0 1 2-2z M9 11h.01 M15 11h.01',
  library:   'M4 19.5A2.5 2.5 0 0 1 6.5 17H20 M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z',
  puzzle:    'M20.24 12.24a6 6 0 0 0-8.49-8.49L5 10.5V19h8.5z M16 8 L2 22 M17.5 15H9',
  workflow:  'M22 12h-4l-3 9L9 3l-3 9H2',
  template:  'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6 M16 13H8 M16 17H8 M10 9H8',
  users:     'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75',
  shield:    'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z',
  model:     'M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z',
  training:  'M18 20V10 M12 20V4 M6 20v-6',
  toggle:    'M12 20h9 M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z',
  language:  'M5 8l6 6 M4 14l6-6 2-2 M2 5h12 M7 2h1 M22 22l-5-10-5 10 M14.5 18h4',
  chart:     'M18 20V10 M12 20V4 M6 20v-6',
  audit:     'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6 M16 13H8 M16 17H8 M10 9H8',
  backup:    'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4 M7 10l5 5 5-5 M12 15V3',
  settings:  'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z',
  collapse:  'M15 18l-6-6 6-6',
  expand:    'M9 18l6-6-6-6',
  logout:    'M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4 M16 17l5-5-5-5 M21 12H9',
  aegis:     '',
}

function Icon({ name, size = 16 }: { name: string; size?: number }) {
  const d = ICONS[name] ?? ''
  const paths = d.split(' M ').map((p, i) => i === 0 ? p : 'M ' + p)
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round"
         aria-hidden="true">
      {paths.map((p, i) => <path key={i} d={p.trim()} />)}
    </svg>
  )
}

function NavGroup({ label, items, collapsed }: {
  label: string
  items: typeof NAV_ITEMS
  collapsed: boolean
}) {
  return (
    <div className="nav-group">
      {!collapsed && <span className="nav-group-label">{label}</span>}
      {items.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          title={collapsed ? item.label : undefined}
        >
          <span className="nav-item-icon"><Icon name={item.icon} size={16} /></span>
          {!collapsed && <span className="nav-item-label">{item.label}</span>}
        </NavLink>
      ))}
    </div>
  )
}

export function Sidebar() {
  const collapsed = useUIStore((s) => s.sidebarCollapsed)
  const toggle    = useUIStore((s) => s.toggleSidebar)
  const logout    = useAuthStore((s) => s.logout)
  const user      = useAuthStore((s) => s.user)

  return (
    <aside className={`sidebar${collapsed ? ' collapsed' : ''}`}>
      {/* Logo */}
      <div className="sidebar-logo">
        <svg width="24" height="24" viewBox="0 0 32 32" fill="none" aria-hidden="true">
          <path d="M16 2 L28 8 L28 16 C28 22.627 22.627 28 16 28 C9.373 28 4 22.627 4 16 L4 8 Z" fill="#4f98a3"/>
          <path d="M16 8 L22 11 L22 16 C22 19.314 19.314 22 16 22 C12.686 22 10 19.314 10 16 L10 11 Z" fill="#0f3638"/>
          <circle cx="16" cy="16" r="3" fill="#cedcd8"/>
        </svg>
        {!collapsed && <span className="sidebar-logo-text">Aegis Studio</span>}
        <button className="sidebar-collapse-btn" onClick={toggle} aria-label="Toggle sidebar">
          <Icon name={collapsed ? 'expand' : 'collapse'} size={14} />
        </button>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <NavGroup label="Application" items={NAV_ITEMS}  collapsed={collapsed} />
        <NavGroup label="Admin"       items={NAV_ADMIN}  collapsed={collapsed} />
        <NavGroup label="Operations"  items={NAV_OPS}    collapsed={collapsed} />
      </nav>

      {/* User footer */}
      <div className="sidebar-footer">
        {user && !collapsed && (
          <div className="sidebar-user">
            <div className="sidebar-avatar">
              {(user.username[0] ?? 'A').toUpperCase()}
            </div>
            <div className="sidebar-user-info">
              <span className="sidebar-user-name">{user.username}</span>
              <span className="sidebar-user-role">{user.roles[0] ?? 'user'}</span>
            </div>
          </div>
        )}
        <button className="nav-item logout-btn" onClick={() => logout()} title="Logout">
          <span className="nav-item-icon"><Icon name="logout" size={16} /></span>
          {!collapsed && <span className="nav-item-label">Logout</span>}
        </button>
      </div>
    </aside>
  )
}
