import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { PageHeader } from '@/components/ui/PageHeader'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { api } from '@/lib/api'
import styles from './AuditPage.module.css'

interface AuditEntry {
  id: string
  timestamp: string
  actor: string
  action: string
  resource: string
  resource_id: string | null
  outcome: 'success' | 'failure' | 'denied'
  ip_address: string | null
  detail: Record<string, unknown> | null
  hmac_valid: boolean
}

const OUTCOME_VARIANT: Record<string, 'success' | 'error' | 'warning' | 'neutral'> = {
  success: 'success',
  failure: 'error',
  denied: 'warning',
}

export function AuditPage() {
  const [search, setSearch] = useState('')
  const [actor, setActor] = useState('')
  const [outcome, setOutcome] = useState<string>('')
  const [page, setPage] = useState(1)
  const PAGE_SIZE = 50

  const { data, isLoading } = useQuery<{ entries: AuditEntry[]; total: number }>({
    queryKey: ['audit', search, actor, outcome, page],
    queryFn: () =>
      api
        .get('/security/audit/query', { params: { q: search, actor, outcome, page, page_size: PAGE_SIZE } })
        .then((r) => r.data),
    placeholderData: (prev) => prev,
  })

  const entries = data?.entries ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / PAGE_SIZE)

  function reset() {
    setSearch(''); setActor(''); setOutcome(''); setPage(1)
  }

  return (
    <div className={styles.page}>
      <PageHeader
        title="Audit Log"
        subtitle={`Log immutabile — ${total.toLocaleString('it-IT')} eventi totali`}
      />

      <div className={styles.filters}>
        <Input placeholder="Cerca azione o risorsa…" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1) }} />
        <Input placeholder="Filtra per attore…" value={actor} onChange={(e) => { setActor(e.target.value); setPage(1) }} />
        <select className={styles.select} value={outcome} onChange={(e) => { setOutcome(e.target.value); setPage(1) }}>
          <option value="">Tutti gli esiti</option>
          <option value="success">Success</option>
          <option value="failure">Failure</option>
          <option value="denied">Denied</option>
        </select>
        <Button variant="ghost" onClick={reset}>Reset</Button>
      </div>

      {isLoading ? <Spinner /> : entries.length === 0 ? (
        <EmptyState icon="file-text" title="Nessun evento" description="Nessun evento corrisponde ai filtri impostati." />
      ) : (
        <>
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Attore</th>
                  <th>Azione</th>
                  <th>Risorsa</th>
                  <th>Esito</th>
                  <th>IP</th>
                  <th>HMAC</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((e) => (
                  <tr key={e.id}>
                    <td className={styles.mono}>{new Date(e.timestamp).toLocaleString('it-IT')}</td>
                    <td className={styles.mono}>{e.actor}</td>
                    <td><Badge variant="neutral">{e.action}</Badge></td>
                    <td className={styles.resource}>
                      <span>{e.resource}</span>
                      {e.resource_id && <span className={styles.resId}>{e.resource_id}</span>}
                    </td>
                    <td><Badge variant={OUTCOME_VARIANT[e.outcome] ?? 'neutral'}>{e.outcome}</Badge></td>
                    <td className={styles.mono}>{e.ip_address ?? '—'}</td>
                    <td>
                      <Badge variant={e.hmac_valid ? 'success' : 'error'}>
                        {e.hmac_valid ? '✓' : '✗'}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className={styles.pagination}>
              <Button variant="ghost" size="sm" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}>‹ Precedente</Button>
              <span className={styles.pageInfo}>Pagina {page} di {totalPages}</span>
              <Button variant="ghost" size="sm" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages}>Successiva ›</Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
