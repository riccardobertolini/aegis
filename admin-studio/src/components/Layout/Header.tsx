import { Sun, Moon } from 'lucide-react'
import { useThemeStore } from '../../store/themeStore'
import { useAuthStore } from '../../store/authStore'
import styles from './Header.module.css'

export default function Header() {
  const { theme, toggle } = useThemeStore()
  const username = useAuthStore(s => s.username)

  return (
    <header className={styles.header}>
      <span className={styles.user}>Logged in as <strong>{username ?? 'admin'}</strong></span>
      <button
        className={styles.themeBtn}
        onClick={toggle}
        aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
      >
        {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
      </button>
    </header>
  )
}
