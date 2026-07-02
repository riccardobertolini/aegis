import type { ReactNode } from 'react'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'
import { useUIStore } from '@/store/ui.store'
import './AppShell.css'

export function AppShell({ children }: { children: ReactNode }) {
  const collapsed = useUIStore((s) => s.sidebarCollapsed)
  return (
    <div className={`app-shell${collapsed ? ' sidebar-collapsed' : ''}`}>
      <Sidebar />
      <div className="app-main">
        <Topbar />
        <main className="app-content">
          {children}
        </main>
      </div>
    </div>
  )
}
