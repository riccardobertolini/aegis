import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import Layout from './components/Layout/Layout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import AssistantsPage from './pages/AssistantsPage'
import TemplatesPage from './pages/TemplatesPage'
import WorkflowsPage from './pages/WorkflowsPage'
import RulesPage from './pages/RulesPage'
import CategoriesPage from './pages/CategoriesPage'
import UsersPage from './pages/UsersPage'
import ModelsPage from './pages/ModelsPage'
import TrainingPage from './pages/TrainingPage'
import FeaturesPage from './pages/FeaturesPage'
import LanguagesPage from './pages/LanguagesPage'
import BackupPage from './pages/BackupPage'
import UsagePage from './pages/UsagePage'
import KnowledgePage from './pages/KnowledgePage'
import PluginsPage from './pages/PluginsPage'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = useAuthStore(s => s.token)
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<RequireAuth><Layout /></RequireAuth>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="assistants" element={<AssistantsPage />} />
        <Route path="templates" element={<TemplatesPage />} />
        <Route path="workflows" element={<WorkflowsPage />} />
        <Route path="rules" element={<RulesPage />} />
        <Route path="categories" element={<CategoriesPage />} />
        <Route path="knowledge" element={<KnowledgePage />} />
        <Route path="plugins" element={<PluginsPage />} />
        <Route path="users" element={<UsersPage />} />
        <Route path="models" element={<ModelsPage />} />
        <Route path="training" element={<TrainingPage />} />
        <Route path="features" element={<FeaturesPage />} />
        <Route path="languages" element={<LanguagesPage />} />
        <Route path="backup" element={<BackupPage />} />
        <Route path="usage" element={<UsagePage />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
