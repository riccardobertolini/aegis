import { useState } from 'react'
import { PageHeader } from '@/components/ui/PageHeader'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Toggle } from '@/components/ui/Toggle'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { useAuthStore } from '@/store/auth.store'
import { useToastStore } from '@/store/toast.store'
import { api } from '@/lib/api-client'
import { useEffect } from 'react'
import styles from './FeatureTogglesPage.module.css'

interface Feature {
  id: string
  name: string
  description: string
  enabled: boolean
  scope: 'global' | 'per_user' | 'per_role'
  created_at: string
  updated_at: string
}

export function FeatureTogglesPage() {
  const [features, setFeatures] = useState<Feature[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState<string | null>(null)
  const hasPermission = useAuthStore((s) => s.hasPermission)
  const addToast = useToastStore((s) => s.add)
  const canEdit = hasPermission('features:write')

  useEffect(() => {
    load()
  }, [])

  async function load() {
    setLoading(true)
    try {
      const data = await api.get<Feature[]>('/features')
      setFeatures(data)
    } catch {
      addToast({ type: 'error', message: 'Failed to load feature toggles' })
    } finally {
      setLoading(false)
    }
  }

  async function toggle(feature: Feature) {
    if (!canEdit) return
    setSaving(feature.id)
    try {
      const updated = await api.patch<Feature>(`/features/${feature.id}`, {
        enabled: !feature.enabled,
      })
      setFeatures((prev) => prev.map((f) => (f.id === updated.id ? updated : f)))
      addToast({
        type: 'success',
        message: `Feature "${updated.name}" ${updated.enabled ? 'enabled' : 'disabled'}`,
      })
    } catch {
      addToast({ type: 'error', message: 'Failed to update feature' })
    } finally {
      setSaving(null)
    }
  }

  return (
    <div className={styles.page}>
      <PageHeader
        title="Feature Toggles"
        description="Enable or disable platform features without redeployment."
        actions={
          <Button variant="ghost" size="sm" onClick={load}>
            Refresh
          </Button>
        }
      />

      {loading ? (
        <div className={styles.center}><Spinner size="lg" /></div>
      ) : features.length === 0 ? (
        <EmptyState
          icon="toggle-left"
          title="No feature toggles"
          description="Feature flags will appear here once registered."
        />
      ) : (
        <div className={styles.grid}>
          {features.map((feature) => (
            <Card key={feature.id} className={styles.card}>
              <div className={styles.cardHeader}>
                <div className={styles.cardInfo}>
                  <h3 className={styles.featureName}>{feature.name}</h3>
                  <Badge variant={feature.scope === 'global' ? 'primary' : 'default'}>
                    {feature.scope}
                  </Badge>
                </div>
                <Toggle
                  checked={feature.enabled}
                  disabled={!canEdit || saving === feature.id}
                  onChange={() => toggle(feature)}
                  aria-label={`Toggle ${feature.name}`}
                />
              </div>
              {feature.description && (
                <p className={styles.description}>{feature.description}</p>
              )}
              <p className={styles.meta}>
                Updated {new Date(feature.updated_at).toLocaleString()}
              </p>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
