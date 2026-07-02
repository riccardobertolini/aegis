import { useState } from 'react'
import { PageHeader } from '@/components/ui/PageHeader'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { useAuthStore } from '@/store/auth.store'
import { useToastStore } from '@/store/toast.store'
import { api } from '@/lib/api-client'
import { useEffect } from 'react'
import styles from './BackupPage.module.css'

interface BackupEntry {
  id: string
  filename: string
  size_bytes: number
  created_at: string
  status: 'ok' | 'partial' | 'error'
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function BackupPage() {
  const [backups, setBackups] = useState<BackupEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [restoreTarget, setRestoreTarget] = useState<BackupEntry | null>(null)
  const hasPermission = useAuthStore((s) => s.hasPermission)
  const addToast = useToastStore((s) => s.add)
  const canWrite = hasPermission('backup:write')
  const canRestore = hasPermission('backup:restore')

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true)
    try {
      const data = await api.get<BackupEntry[]>('/security/backup/list')
      setBackups(data)
    } catch {
      addToast({ type: 'error', message: 'Failed to load backups' })
    } finally {
      setLoading(false)
    }
  }

  async function createBackup() {
    setCreating(true)
    try {
      const entry = await api.post<BackupEntry>('/security/backup/create')
      setBackups((prev) => [entry, ...prev])
      addToast({ type: 'success', message: 'Backup created successfully' })
    } catch {
      addToast({ type: 'error', message: 'Backup creation failed' })
    } finally {
      setCreating(false)
    }
  }

  async function confirmRestore() {
    if (!restoreTarget) return
    try {
      await api.post(`/security/backup/restore/${restoreTarget.id}`)
      addToast({ type: 'success', message: `Restore from ${restoreTarget.filename} initiated` })
    } catch {
      addToast({ type: 'error', message: 'Restore failed' })
    } finally {
      setRestoreTarget(null)
    }
  }

  const statusVariant = (s: BackupEntry['status']) =>
    s === 'ok' ? 'success' : s === 'partial' ? 'warning' : 'error'

  return (
    <div className={styles.page}>
      <PageHeader
        title="Backup & Restore"
        description="Encrypted local backups (.aeb). All data stays air-gapped."
        actions={
          canWrite && (
            <Button variant="primary" size="sm" onClick={createBackup} disabled={creating}>
              {creating ? <Spinner size="sm" /> : 'Create Backup'}
            </Button>
          )
        }
      />

      {loading ? (
        <div className={styles.center}><Spinner size="lg" /></div>
      ) : backups.length === 0 ? (
        <EmptyState
          icon="archive"
          title="No backups yet"
          description="Create your first encrypted backup to protect your data."
          action={canWrite ? { label: 'Create Backup', onClick: createBackup } : undefined}
        />
      ) : (
        <div className={styles.list}>
          {backups.map((backup) => (
            <Card key={backup.id} className={styles.item}>
              <div className={styles.itemMain}>
                <div className={styles.itemInfo}>
                  <span className={styles.filename}>{backup.filename}</span>
                  <span className={styles.meta}>
                    {formatBytes(backup.size_bytes)} · {new Date(backup.created_at).toLocaleString()}
                  </span>
                </div>
                <div className={styles.itemActions}>
                  <Badge variant={statusVariant(backup.status)}>{backup.status}</Badge>
                  {canRestore && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setRestoreTarget(backup)}
                    >
                      Restore
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {restoreTarget && (
        <ConfirmDialog
          title="Restore Backup"
          message={`Restore from "${restoreTarget.filename}"? Current data will be overwritten.`}
          confirmLabel="Restore"
          variant="warning"
          onConfirm={confirmRestore}
          onCancel={() => setRestoreTarget(null)}
        />
      )}
    </div>
  )
}
