import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Bot, FileText, GitBranch, Shield,
  Tag, BookOpen, Puzzle, Users, Cpu, Dumbbell,
  ToggleLeft, Globe, Archive, BarChart2, LogOut
} from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import { authApi } from '../../lib/api'
import styles from './Sidebar.module.css'

const NAV = [
  { to: 'dashboard',  label: 'Dashboard',    icon: LayoutDashboard },
  { to: 'assistants', label: 'Assistants',   icon: Bot },
  { to: 'templates',  label: 'Templates',    icon: FileText },
  { to: 'workflows',  label: 'Workflows',    icon: GitBranch },
  { to: 'rules',      label: 'Rules',        icon: Shield },
  { to: 'categories', label: 'Categories',   icon: Tag },
  { to: 'knowledge',  label: 'Knowledge',    icon: BookOpen },
  { to: 'plugins',    label: 'Plugins',      icon: Puzzle },
  { to: 'users',      label: 'Users',        icon: Users },
  { to: 'models',     label: 'Models',       icon: Cpu },
  { to: 'training',   label: 'Training',     icon: Dumbbell },
  { to: 'features',   label: 'Features',     icon: ToggleLeft },
  { to: 'languages',  label: 'Languages',    icon: Globe },
  { to: 'backup',     label: 'Backup',       icon: Archive },
  { to: 'usage',      label: 'Usage',        icon: BarChart2 },
]

export default function Sidebar() {
  const logout = useAuthStore(s => s.logout)

  async function handleLogout() {
    try { await authApi.logout() } catch {}
    logout()
  }

  return (
    <aside className={styles.sidebar}>
      <div className={styles.logo}>
        <svg viewBox="0 0 24 24" fill="none" width="28" height="28" aria-label="Aegis">
          <rect width="24" height="24" rx="6" fill="var(--color-primary)"/>
          <path d="M6 17 L12 7 L18 17" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M8.5 13.5 L15.5 13.5" stroke="white" strokeWidth="2" strokeLinecap="round"/>
        </svg>
        <span className={styles.logoText}>Aegis</span>
      </div>
      <nav className={styles.nav}>
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={`/${to}`}
            className={({ isActive }) =>
              [styles.navItem, isActive ? styles.active : ''].join(' ')}
          >
            <Icon size={16} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
      <button className={styles.logoutBtn} onClick={handleLogout}>
        <LogOut size={16} />
        <span>Logout</span>
      </button>
    </aside>
  )
}
