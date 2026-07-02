import { useState, useEffect } from 'react'
import { PageHeader } from '@/components/ui/PageHeader'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { FormField } from '@/components/ui/FormField'
import { Input } from '@/components/ui/Input'
import { Toggle } from '@/components/ui/Toggle'
import { Spinner } from '@/components/ui/Spinner'
import { useAuthStore } from '@/store/auth.store'
import { useToastStore } from '@/store/toast.store'
import { api } from '@/lib/api-client'
import styles from './SettingsPage.module.css'

interface AppSettings {
  app_name: string
  default_language: string
  session_timeout_minutes: number
  max_sessions_per_user: number
  audit_retention_days: number
  allow_registration: boolean
  require_mfa: boolean
  inference_timeout_seconds: number
  max_document_size_mb: number
}

export function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings | null>(null)
  const [draft, setDraft] = useState<AppSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const hasPermission = useAuthStore((s) => s.hasPermission)
  const addToast = useToastStore((s) => s.add)
  const canEdit = hasPermission('admin:settings:write')

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true)
    try {
      const data = await api.get<AppSettings>('/admin/settings')
      setSettings(data)
      setDraft({ ...data })
    } catch {
      addToast({ type: 'error', message: 'Failed to load settings' })
    } finally {
      setLoading(false)
    }
  }

  async function save() {
    if (!draft) return
    setSaving(true)
    try {
      const updated = await api.put<AppSettings>('/admin/settings', draft)
      setSettings(updated)
      setDraft({ ...updated })
      addToast({ type: 'success', message: 'Settings saved' })
    } catch {
      addToast({ type: 'error', message: 'Failed to save settings' })
    } finally {
      setSaving(false)
    }
  }

  function set<K extends keyof AppSettings>(key: K, value: AppSettings[K]) {
    setDraft((prev) => prev ? { ...prev, [key]: value } : prev)
  }

  const isDirty = JSON.stringify(settings) !== JSON.stringify(draft)

  if (loading) return <div className={styles.center}><Spinner size="lg" /></div>
  if (!draft) return null

  return (
    <div className={styles.page}>
      <PageHeader
        title="Settings"
        description="Platform-wide configuration. All settings stored locally."
        actions={
          canEdit && (
            <Button
              variant="primary"
              size="sm"
              onClick={save}
              disabled={!isDirty || saving}
            >
              {saving ? <Spinner size="sm" /> : 'Save Changes'}
            </Button>
          )
        }
      />

      <div className={styles.sections}>
        <Card className={styles.section}>
          <h2 className={styles.sectionTitle}>General</h2>
          <div className={styles.fields}>
            <FormField label="Application Name">
              <Input
                value={draft.app_name}
                onChange={(e) => set('app_name', e.target.value)}
                disabled={!canEdit}
              />
            </FormField>
            <FormField label="Default Language">
              <Input
                value={draft.default_language}
                onChange={(e) => set('default_language', e.target.value)}
                disabled={!canEdit}
                placeholder="e.g. en"
              />
            </FormField>
          </div>
        </Card>

        <Card className={styles.section}>
          <h2 className={styles.sectionTitle}>Security</h2>
          <div className={styles.fields}>
            <FormField label="Session Timeout (minutes)">
              <Input
                type="number"
                value={String(draft.session_timeout_minutes)}
                onChange={(e) => set('session_timeout_minutes', Number(e.target.value))}
                disabled={!canEdit}
                min="5"
                max="1440"
              />
            </FormField>
            <FormField label="Max Sessions per User">
              <Input
                type="number"
                value={String(draft.max_sessions_per_user)}
                onChange={(e) => set('max_sessions_per_user', Number(e.target.value))}
                disabled={!canEdit}
                min="1"
                max="20"
              />
            </FormField>
            <FormField label="Audit Log Retention (days)">
              <Input
                type="number"
                value={String(draft.audit_retention_days)}
                onChange={(e) => set('audit_retention_days', Number(e.target.value))}
                disabled={!canEdit}
                min="30"
              />
            </FormField>
            <FormField label="Allow Self-Registration">
              <Toggle
                checked={draft.allow_registration}
                onChange={(v) => set('allow_registration', v)}
                disabled={!canEdit}
              />
            </FormField>
            <FormField label="Require MFA">
              <Toggle
                checked={draft.require_mfa}
                onChange={(v) => set('require_mfa', v)}
                disabled={!canEdit}
              />
            </FormField>
          </div>
        </Card>

        <Card className={styles.section}>
          <h2 className={styles.sectionTitle}>Inference & Documents</h2>
          <div className={styles.fields}>
            <FormField label="Inference Timeout (seconds)">
              <Input
                type="number"
                value={String(draft.inference_timeout_seconds)}
                onChange={(e) => set('inference_timeout_seconds', Number(e.target.value))}
                disabled={!canEdit}
                min="5"
                max="300"
              />
            </FormField>
            <FormField label="Max Document Size (MB)">
              <Input
                type="number"
                value={String(draft.max_document_size_mb)}
                onChange={(e) => set('max_document_size_mb', Number(e.target.value))}
                disabled={!canEdit}
                min="1"
                max="500"
              />
            </FormField>
          </div>
        </Card>
      </div>
    </div>
  )
}
