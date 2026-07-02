import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { featuresApi } from '@/lib/api'
import { useToastStore } from '@/store/toast.store'
import { PageHeader } from '@/components/ui/PageHeader'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'

export function FeaturesPage() {
  const qc = useQueryClient()
  const toast = useToastStore()

  const { data, isLoading } = useQuery({ queryKey: ['features'], queryFn: featuresApi.list })

  const toggleMut = useMutation({
    mutationFn: ({ key, enabled, description }: { key: string; enabled: boolean; description: string }) =>
      featuresApi.set(key, enabled, description),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['features'] }),
    onError: (e: Error) => toast.error(e.message),
  })

  if (isLoading) return <PageSpinner />

  return (
    <div>
      <PageHeader title="Feature Toggles" subtitle="Abilita o disabilita funzionalità in tempo reale" />

      {!data?.length ? (
        <EmptyState icon="🔧" title="Nessun toggle" description="Nessuna funzionalità configurata." />
      ) : (
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {data.map(f => (
            <Card key={f.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 600, fontFamily: 'monospace', fontSize: '0.9375rem' }}>{f.key}</div>
                {f.description && <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', marginTop: 2 }}>{f.description}</div>}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Badge label={f.enabled ? 'ON' : 'OFF'} color={f.enabled ? 'green' : 'gray'} />
                <label style={{ position: 'relative', display: 'inline-block', width: 44, height: 24 }}>
                  <input
                    type="checkbox"
                    checked={f.enabled}
                    onChange={() => toggleMut.mutate({ key: f.key, enabled: !f.enabled, description: f.description })}
                    style={{ opacity: 0, width: 0, height: 0 }}
                  />
                  <span style={{
                    position: 'absolute', cursor: 'pointer', inset: 0,
                    background: f.enabled ? 'var(--color-primary)' : 'var(--color-border)',
                    borderRadius: 24, transition: '0.2s',
                  }} />
                  <span style={{
                    position: 'absolute', content: '', height: 18, width: 18,
                    left: f.enabled ? 22 : 3, bottom: 3,
                    background: '#fff', borderRadius: '50%', transition: '0.2s',
                  }} />
                </label>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
