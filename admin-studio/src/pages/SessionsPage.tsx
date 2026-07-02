import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { PageHeader } from '@/components/ui/PageHeader'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { useToastStore } from '@/store/toast.store'
import { useAuthStore } from '@/store/auth.store'
import { api } from '@/lib/api'
import { useState } from 'react'
import styles from './SessionsPage.module.css'

interface Session {
  id: string
  user_id: string
  username: string
  created_at: string
  expires_at: string
  ip_address: string | null
  user_agent: string | null
  is_current: boolean
}

export function SessionsPage() {
  const qc = useQueryClient()
  const addToast = useToastStore((s) => s.addToast)
  const currentUserId = useAuthStore((s) => s.user?.id)
  const [revokeAll, setRevokeAll] = useState(false)

  const { data: sessions = [], isLoading } = useQuery<Session[]>({
    queryKey: ['sessions'],
    queryFn: () => api.get('/security/sessions').then((r) => r.data),
  })

  const revokeMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/security/sessions/${id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['sessions'] }); addToast({ type: 'success', message: 'Sessione revocata' }) },
    onError: () => addToast({ type: 'error', message: 'Errore revoca sessione' }),
  })

  const revokeAllMutation = useMutation({
    mutationFn: () => api.delete('/security/sessions'),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['sessions'] }); addToast({ type: 'success', message: 'Tutte le sessioni revocate' }); setRevokeAll(false) },
    onError: () => addToast({ type: 'error', message: 'Errore' }),
  })

  return (
    <div className={styles.page}>
      <PageHeader
        title="Sessioni attive"
        subtitle="Monitora e revoca le sessioni utente"
        actions={
          <Button variant="danger" onClick={() => setRevokeAll(true)} disabled={sessions.length === 0}>
            Revoca tutte
          </Button>
        }
      />

      {isLoading ? <Spinner /> : sessions.length === 0 ? (
        <EmptyState icon="log-out" title="Nessuna sessione" description="Non ci sono sessioni attive al momento." />
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Utente</th>
                <th>Creata</th>
                <th>Scade</th>
                <th>IP</th>
                <th>User Agent</th>
                <th>Stato</th>
                <th>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((s) => (
                <tr key={s.id}>
                  <td className={styles.mono}>{s.username}</td>
                  <td className={styles.muted}>{new Date(s.created_at).toLocaleString('it-IT')}</td>
                  <td className={styles.muted}>{new Date(s.expires_at).toLocaleString('it-IT')}</td>
                  <td className={styles.mono}>{s.ip_address ?? '—'}</td>
                  <td className={styles.ua} title={s.user_agent ?? ''}>{s.user_agent ? s.user_agent.substring(0, 40) + '…' : '—'}</td>
                  <td>
                    {s.is_current
                      ? <Badge variant="success">Corrente</Badge>
                      : new Date(s.expires_at) < new Date()
                        ? <Badge variant="error">Scaduta</Badge>
                        : <Badge variant="neutral">Attiva</Badge>}
                  </td>
                  <td>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => revokeMutation.mutate(s.id)}
                      disabled={s.is_current}
                      loading={revokeMutation.isPending}
                    >
                      Revoca
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <ConfirmDialog
        open={revokeAll}
        title="Revoca tutte le sessioni"
        message="Verranno terminate tutte le sessioni attive di tutti gli utenti. Questa azione non può essere annullata."
        confirmLabel="Revoca tutte"
        onConfirm={() => revokeAllMutation.mutate()}
        onCancel={() => setRevokeAll(false)}
        danger
      />
    </div>
  )
}
