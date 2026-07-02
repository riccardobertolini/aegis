import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/auth.store'
import { useUIStore } from '@/store/ui.store'
import { AppShell } from '@/components/layout/AppShell'
import { LoginPage } from '@/pages/LoginPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { AssistantsPage } from '@/pages/AssistantsPage'
import { AssistantDetailPage } from '@/pages/AssistantDetailPage'
import { KnowledgePage } from '@/pages/KnowledgePage'
import { PluginsPage } from '@/pages/PluginsPage'
import { UsersPage } from '@/pages/UsersPage'
import { RolesPage } from '@/pages/RolesPage'
import { ModelsPage } from '@/pages/ModelsPage'
import { TrainingPage } from '@/pages/TrainingPage'
import { WorkflowsPage } from '@/pages/WorkflowsPage'
import { FeatureTogglesPage } from '@/pages/FeatureTogglesPage'
import { LanguagesPage } from '@/pages/LanguagesPage'
import { BackupPage } from '@/pages/BackupPage'
import { AuditPage } from '@/pages/AuditPage'
import { MonitoringPage } from '@/pages/MonitoringPage'
import { TemplatesPage } from '@/pages/TemplatesPage'
import { SettingsPage } from '@/pages/SettingsPage'
import { ToastContainer } from '@/components/ui/ToastContainer'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  const applyTheme = useUIStore((s) => s.applyTheme)
  const fetchMe    = useAuthStore((s) => s.fetchMe)
  const token      = useAuthStore((s) => s.token)

  useEffect(() => { applyTheme() }, [])
  useEffect(() => { if (token) fetchMe() }, [token])

  return (
    <>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/*"
          element={
            <RequireAuth>
              <AppShell>
                <Routes>
                  <Route index element={<Navigate to="/dashboard" replace />} />
                  <Route path="dashboard"          element={<DashboardPage />} />
                  <Route path="assistants"         element={<AssistantsPage />} />
                  <Route path="assistants/:id"     element={<AssistantDetailPage />} />
                  <Route path="knowledge"          element={<KnowledgePage />} />
                  <Route path="plugins"            element={<PluginsPage />} />
                  <Route path="users"              element={<UsersPage />} />
                  <Route path="roles"              element={<RolesPage />} />
                  <Route path="models"             element={<ModelsPage />} />
                  <Route path="training"           element={<TrainingPage />} />
                  <Route path="workflows"          element={<WorkflowsPage />} />
                  <Route path="features"           element={<FeatureTogglesPage />} />
                  <Route path="languages"          element={<LanguagesPage />} />
                  <Route path="backup"             element={<BackupPage />} />
                  <Route path="audit"              element={<AuditPage />} />
                  <Route path="monitoring"         element={<MonitoringPage />} />
                  <Route path="templates"          element={<TemplatesPage />} />
                  <Route path="settings"           element={<SettingsPage />} />
                  <Route path="*"                  element={<Navigate to="/dashboard" replace />} />
                </Routes>
              </AppShell>
            </RequireAuth>
          }
        />
      </Routes>
      <ToastContainer />
    </>
  )
}
