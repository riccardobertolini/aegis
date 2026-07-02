import { clsx } from 'clsx'
import styles from './Badge.module.css'

type Variant = 'default' | 'success' | 'warning' | 'error' | 'primary'

export function Badge({ children, variant = 'default' }: { children: React.ReactNode; variant?: Variant }) {
  return <span className={clsx(styles.badge, styles[variant])}>{children}</span>
}
