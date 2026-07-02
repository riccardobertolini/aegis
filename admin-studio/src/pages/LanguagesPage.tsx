import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { languagesApi, type LanguageUpsert } from '@/lib/api'
import { useToastStore } from '@/store/toast.store'
import { PageHeader } from '@/components/ui/PageHeader'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { PageSpinner } from '@/components/ui/Spinner'
import { Modal } from '@/components/ui/Modal'
import { FormField, Input } from '@/components/ui/FormField'
import { EmptyState } from '@/components/ui/EmptyState'

export function LanguagesPage() {
  const qc = useQueryClient()
  const toast = useToastStore()
  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm] = useState<LanguageUpsert>({ code: '', label: '', is_enabled: true, is_default: false })

  const { data, isLoading } = useQuery({ queryKey: ['languages'], queryFn: languagesApi.list })

  const upsertMut = useMutation({
    mutationFn: languagesApi.upsert,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['languages'] }); setShowAdd(false); toast.success('Lingua salvata') },
    onError: (e: Error) => toast.error(e.message),
  })

  const toggleMut = useMutation({
    mutationFn: ({ code, label, is_enabled }: LanguageUpsert) => languagesApi.upsert({ code, label, is_enabled }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['languages'] }),
  })

  if (isLoading) return <PageSpinner />

  return (
    <div>
      <PageHeader title="Lingue" subtitle="Gestione lingue supportate"
        actions={<Button onClick={() => setShowAdd(true)}>+ Aggiungi</Button>} />

      {!data?.length ? (
        <EmptyState icon="🌍" title="Nessuna lingua" description="Aggiungi le lingue supportate dalla piattaforma." actionLabel="+ Aggiungi" onAction={() => setShowAdd(true)} />
      ) : (
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {data.map(l => (
            <Card key={l.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span style={{ fontSize: '1.5rem' }}>🌐</span>
                <div>
                  <div style={{ fontWeight: 600 }}>{l.label} <span style={{ color: 'var(--color-text-muted)', fontFamily: 'monospace', fontSize: '0.875rem' }}>({l.code})</span></div>
                  <div style={{ marginTop: 4, display: 'flex', gap: 6 }}>
                    {l.is_default && <Badge label="default" color="blue" />}
                    <Badge label={l.is_enabled ? 'abilitata' : 'disabilitata'} color={l.is_enabled ? 'green' : 'gray'} />
                  </div>
                </div>
              </div>
              <Button size="sm" variant="ghost" onClick={() => toggleMut.mutate({ code: l.code, label: l.label, is_enabled: !l.is_enabled })}>
                {l.is_enabled ? 'Disabilita' : 'Abilita'}
              </Button>
            </Card>
          ))}
        </div>
      )}

      <Modal open={showAdd} onClose={() => setShowAdd(false)} title="Aggiungi lingua"
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowAdd(false)}>Annulla</Button>
            <Button loading={upsertMut.isPending} onClick={() => upsertMut.mutate(form)}>Salva</Button>
          </>
        }>
        <FormField label="Codice (ISO 639-1)" required><Input value={form.code} onChange={e => setForm(f => ({ ...f, code: e.target.value }))} placeholder="it" /></FormField>
        <FormField label="Nome"><Input value={form.label} onChange={e => setForm(f => ({ ...f, label: e.target.value }))} placeholder="Italiano" /></FormField>
        <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
          <label style={{ display: 'flex', gap: 6, fontSize: '0.875rem' }}>
            <input type="checkbox" checked={form.is_enabled} onChange={e => setForm(f => ({ ...f, is_enabled: e.target.checked }))} /> Abilitata
          </label>
          <label style={{ display: 'flex', gap: 6, fontSize: '0.875rem' }}>
            <input type="checkbox" checked={form.is_default} onChange={e => setForm(f => ({ ...f, is_default: e.target.checked }))} /> Default
          </label>
        </div>
      </Modal>
    </div>
  )
}
