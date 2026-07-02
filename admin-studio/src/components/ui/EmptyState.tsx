import { type LucideIcon } from 'lucide-react'
import styles from './EmptyState.module.css'

interface Props {
  icon: LucideIcon
  title: string
  description: string
  action?: React.ReactNode
}

export function EmptyState({ icon: Icon, title, description, action }: Props) {
  return (
    <div className={styles.empty}>
      <div className={styles.icon}><Icon size={40} /></div>
      <h3 className={styles.title}>{title}</h3>
      <p className={styles.desc}>{description}</p>
      {action && <div className={styles.action}>{action}</div>}
    </div>
  )
}
