import { useQuery } from '@tanstack/react-query'
import { systemApi, usageApi } from '@/lib/api'
import { PageHeader } from '@/components/ui/PageHeader'
import { Card } from '@/components/ui/Card'
import { PageSpinner } from '@/components/ui/Spinner'
import { Badge } from '@/components/ui/Badge'

export function DashboardPage() {
  const { data: health, isLoading: hLoading } = useQuery({
    queryKey: ['health'],
    queryFn: systemApi.health,
    refetchInterval: 30_000,
  })

  const { data: stats } = useQuery({
    queryKey: ['usage-stats'],
    queryFn: () => usageApi.stats(),
    refetchInterval: 60_000,
  })

  if (hLoading) return <PageSpinner />

  const statusColor = health?.status === 'healthy' ? 'green' : health?.status === 'degraded' ? 'orange' : 'red'

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Stato del sistema Aegis" />

      {/* Status */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <Card>
          <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>Stato sistema</div>
          <Badge label={health?.status ?? 'unknown'} color={statusColor} />
          {health?.warnings && health.warnings.length > 0 && (
            <ul style={{ marginTop: '0.75rem', paddingLeft: '1.2rem', fontSize: '0.8125rem', color: 'var(--color-warning)' }}>
              {health.warnings.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          )}
        </Card>

        {stats && (
          <>
            <Card>
              <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>Richieste totali</div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700 }}>{stats.total_events.toLocaleString()}</div>
            </Card>
            <Card>
              <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>Token totali</div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700 }}>{stats.total_tokens.toLocaleString()}</div>
            </Card>
            <Card>
              <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>Latenza media</div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700 }}>{stats.avg_duration_ms} ms</div>
            </Card>
          </>
        )}
      </div>

      {/* Components */}
      {health?.components && (
        <Card>
          <h3 style={{ margin: '0 0 1rem', fontSize: '0.9375rem', fontWeight: 600 }}>Componenti</h3>
          <table style={{ width: '100%', fontSize: '0.875rem', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-divider)' }}>
                <th style={{ textAlign: 'left', padding: '0.4rem 0.5rem', fontWeight: 600 }}>Componente</th>
                <th style={{ textAlign: 'left', padding: '0.4rem 0.5rem', fontWeight: 600 }}>Stato</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(health.components).map(([k, v]) => (
                <tr key={k} style={{ borderBottom: '1px solid var(--color-divider)' }}>
                  <td style={{ padding: '0.4rem 0.5rem', fontWeight: 500 }}>{k}</td>
                  <td style={{ padding: '0.4rem 0.5rem', color: 'var(--color-text-muted)' }}>{v}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  )
}
