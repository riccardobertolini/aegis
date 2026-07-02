import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { PageHeader } from '@/components/ui/PageHeader'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { useToastStore } from '@/store/toast.store'
import { api } from '@/lib/api'
import styles from './PluginsPage.module.css'

interface Plugin {
  id: string
  name: string
  version: string
  description: string
  author: string
  is_enabled: boolean
  is_system: boolean
  capabilities: string[]
  loaded_at: string | null
}

export function PluginsPage() {
  const qc = useQueryClient()
  const addToast = useToastStore((s) => s.addToast)

  const { data: plugins = [], isLoading } = useQuery<Plugin[]>({
    queryKey: ['plugins'],
    queryFn: () => api.get('/plugins').then((r) => r.data),
  })

  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      api.patch(`/plugins/${id}`, { is_enabled: enabled }),
    onSuccess: (_, { enabled }) => {
      qc.invalidateQueries({ queryKey: ['plugins'] })
      addToast({ type: 'success', message: enabled ? 'Plugin abilitato' : 'Plugin disabilitato' })
    },
    onError: () => addToast({ type: 'error', message: 'Errore toggle plugin' }),
  })

  const reloadMutation = useMutation({
    mutationFn: (id: string) => api.post(`/plugins/${id}/reload`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['plugins'] }); addToast({ type: 'success', message: 'Plugin ricaricato' }) },
    onError: () => addToast({ type: 'error', message: 'Errore reload' }),
  })

  const enabledCount = plugins.filter((p) => p.is_enabled).length

  return (
    <div className={styles.page}>
      <PageHeader
        title="Plugin"
        subtitle={`${enabledCount} di ${plugins.length} plugin abilitati`}
      />

      {isLoading ? <Spinner /> : plugins.length === 0 ? (
        <EmptyState icon="puzzle" title="Nessun plugin" description="Copia i plugin nella cartella plugins/ per vederli qui." />
      ) : (
        <div className={styles.grid}>
          {plugins.map((p) => (
            <div key={p.id} className={`${styles.card} ${p.is_enabled ? styles.cardEnabled : ''}`}>
              <div className={styles.cardHeader}>
                <div>
                  <div className={styles.pluginName}>{p.name}</div>
                  <div className={styles.pluginMeta}>v{p.version} &mdash; {p.author}</div>
                </div>
                <div className={styles.cardBadges}>
                  {p.is_system && <Badge variant="warning">Sistema</Badge>}
                  <Badge variant={p.is_enabled ? 'success' : 'neutral'}>{p.is_enabled ? 'Attivo' : 'Disattivo'}</Badge>
                </div>
              </div>

              <p className={styles.pluginDesc}>{p.description}</p>

              {p.capabilities.length > 0 && (
                <div className={styles.caps}>
                  {p.capabilities.map((c) => <Badge key={c} variant="neutral" size="sm">{c}</Badge>)}
                </div>
              )}

              <div className={styles.cardActions}>
                <Button
                  variant={p.is_enabled ? 'ghost' : 'primary'}
                  size="sm"
                  onClick={() => toggleMutation.mutate({ id: p.id, enabled: !p.is_enabled })}
                  disabled={p.is_system}
                >
                  {p.is_enabled ? 'Disabilita' : 'Abilita'}
                </Button>
                {p.is_enabled && (
                  <Button variant="ghost" size="sm" onClick={() => reloadMutation.mutate(p.id)}>Ricarica</Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
