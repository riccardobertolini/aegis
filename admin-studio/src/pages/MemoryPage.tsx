import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { PageHeader } from '@/components/ui/PageHeader'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Input } from '@/components/ui/Input'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { useToastStore } from '@/store/toast.store'
import { api } from '@/lib/api'
import styles from './MemoryPage.module.css'

interface MemoryEntry {
  id: string
  session_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  tokens: number
  created_at: string
  metadata: Record<string, unknown> | null
}

interface MemoryStats {
  total_entries: number
  total_tokens: number
  sessions: number
  oldest_entry: string | null
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('it-IT', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

const ROLE_BADGE: Record<string, 'neutral' | 'success' | 'warning'> = {
  user: 'neutral',
  assistant: 'success',
  system: 'warning',
}

export function MemoryPage() {
  const qc = useQueryClient()
  const addToast = useToastStore((s) => s.addToast)
  const [sessionFilter, setSessionFilter] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<MemoryEntry | null>(null)
  const [flushTarget, setFlushTarget] = useState<string | null>(null)
  const [flushAll, setFlushAll] = useState(false)
  const [page, setPage] = useState(1)
  const PAGE_SIZE = 25

  const { data: stats } = useQuery<MemoryStats>({
    queryKey: ['memory-stats'],
    queryFn: () => api.get('/memory/stats').then((r) => r.data),
  })

  const { data: entries = [], isLoading } = useQuery<MemoryEntry[]>({
    queryKey: ['memory', sessionFilter, page],
    queryFn: () =>
      api.get('/memory', {
        params: {
          session_id: sessionFilter || undefined,
          limit: PAGE_SIZE,
          offset: (page - 1) * PAGE_SIZE,
        },
      }).then((r) => r.data),
    keepPreviousData: true,
  })

  const deleteEntryMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/memory/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['memory'] })
      qc.invalidateQueries({ queryKey: ['memory-stats'] })
      addToast({ type: 'success', message: 'Entry rimossa' })
      setDeleteTarget(null)
    },
    onError: () => addToast({ type: 'error', message: 'Errore eliminazione entry' }),
  })

  const flushSessionMutation = useMutation({
    mutationFn: (sessionId: string) => api.delete(`/memory/session/${sessionId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['memory'] })
      qc.invalidateQueries({ queryKey: ['memory-stats'] })
      addToast({ type: 'success', message: 'Sessione svuotata' })
      setFlushTarget(null)
    },
    onError: () => addToast({ type: 'error', message: 'Errore flush sessione' }),
  })

  const flushAllMutation = useMutation({
    mutationFn: () => api.delete('/memory'),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['memory'] })
      qc.invalidateQueries({ queryKey: ['memory-stats'] })
      addToast({ type: 'success', message: 'Memoria svuotata' })
      setFlushAll(false)
    },
    onError: () => addToast({ type: 'error', message: 'Errore flush memoria' }),
  })

  const totalPages = stats ? Math.ceil(stats.total_entries / PAGE_SIZE) : 1

  return (
    <div className={styles.page}>
      <PageHeader
        title="Memoria"
        subtitle="Cronologia delle conversazioni e stato della memoria contestuale"
        actions={
          <Button variant="ghost" onClick={() => setFlushAll(true)}>
            Svuota tutto
          </Button>
        }
      />

      {/* Stats bar */}
      {stats && (
        <div className={styles.statsBar}>
          <div className={styles.statCard}>
            <span className={styles.statValue}>{stats.total_entries.toLocaleString()}</span>
            <span className={styles.statLabel}>Entry totali</span>
          </div>
          <div className={styles.statCard}>
            <span className={styles.statValue}>{stats.total_tokens.toLocaleString()}</span>
            <span className={styles.statLabel}>Token totali</span>
          </div>
          <div className={styles.statCard}>
            <span className={styles.statValue}>{stats.sessions}</span>
            <span className={styles.statLabel}>Sessioni</span>
          </div>
          {stats.oldest_entry && (
            <div className={styles.statCard}>
              <span className={styles.statValue}>{formatDate(stats.oldest_entry)}</span>
              <span className={styles.statLabel}>Prima entry</span>
            </div>
          )}
        </div>
      )}

      {/* Toolbar */}
      <div className={styles.toolbar}>
        <Input
          placeholder="Filtra per session_id…"
          value={sessionFilter}
          onChange={(e) => { setSessionFilter(e.target.value); setPage(1) }}
          style={{ maxWidth: 300 }}
        />
        {sessionFilter && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setFlushTarget(sessionFilter)}
          >
            Flush sessione
          </Button>
        )}
      </div>

      {/* Table */}
      {isLoading ? <Spinner /> : entries.length === 0 ? (
        <EmptyState
          icon="dashboard"
          title="Nessuna entry in memoria"
          description="La memoria si popola automaticamente durante le conversazioni con gli assistenti."
        />
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Ruolo</th>
                <th>Contenuto</th>
                <th>Session ID</th>
                <th>Token</th>
                <th>Data</th>
                <th>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.id}>
                  <td><Badge variant={ROLE_BADGE[e.role] ?? 'neutral'}>{e.role}</Badge></td>
                  <td className={styles.contentCell}>
                    <span className={styles.contentPreview}>{e.content}</span>
                  </td>
                  <td className={styles.sessionCell}>
                    <code className={styles.code}>{e.session_id}</code>
                  </td>
                  <td className={styles.muted}>{e.tokens}</td>
                  <td className={styles.muted}>{formatDate(e.created_at)}</td>
                  <td>
                    <Button variant="ghost" size="sm" onClick={() => setDeleteTarget(e)}>
                      Rimuovi
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className={styles.pagination}>
          <Button variant="ghost" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            ← Precedente
          </Button>
          <span className={styles.pageInfo}>Pagina {page} di {totalPages}</span>
          <Button variant="ghost" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
            Successiva →
          </Button>
        </div>
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        title="Rimuovi entry"
        message={`Rimuovere questa entry di memoria dalla sessione "${deleteTarget?.session_id}"?`}
        confirmLabel="Rimuovi"
        onConfirm={() => deleteTarget && deleteEntryMutation.mutate(deleteTarget.id)}
        onCancel={() => setDeleteTarget(null)}
        danger
      />

      <ConfirmDialog
        open={!!flushTarget}
        title="Flush sessione"
        message={`Eliminare tutta la memoria della sessione "${flushTarget}"? L'operazione è irreversibile.`}
        confirmLabel="Flush"
        onConfirm={() => flushTarget && flushSessionMutation.mutate(flushTarget)}
        onCancel={() => setFlushTarget(null)}
        danger
      />

      <ConfirmDialog
        open={flushAll}
        title="Svuota tutta la memoria"
        message="Eliminare tutte le entry di memoria di tutte le sessioni? L'operazione è irreversibile."
        confirmLabel="Svuota tutto"
        onConfirm={() => flushAllMutation.mutate()}
        onCancel={() => setFlushAll(false)}
        danger
      />
    </div>
  )
}
