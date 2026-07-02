import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { rulesApi, type RuleCreate } from '@/lib/api'
import { useToastStore } from '@/store/toast.store'
import { PageHeader } from '@/components/ui/PageHeader'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageSpinner } from '@/components/ui/Spinner'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { Modal } from '@/components/ui/Modal'
import { FormField, Input } from '@/components/ui/FormField'

export function RulesPage() {
  const qc = useQueryClient()
  const toast = useToastStore()
  const [showCreate, setShowCreate] = useState(false)
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [form, setForm] = useState<RuleCreate>({ name: '', condition: '', action: '', priority: 0 })

  const { data, isLoading } = useQuery({ queryKey: ['rules'], queryFn: rulesApi.list })

  const createMut = useMutation({
    mutationFn: rulesApi.create,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['rules'] }); setShowCreate(false); toast.success('Regola creata') },
    onError: (e: Error) => toast.error(e.message),
  })

  const deleteMut = useMutation({
    mutationFn: (id: number) => rulesApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['rules'] }); setDeleteId(null); toast.success('Eliminata') },
    onError: (e: Error) => toast.error(e.message),
  })

  if (isLoading) return <PageSpinner />

  return (
    <div>
      <PageHeader title="Regole" subtitle={`${data?.length ?? 0} regole`}
        actions={<Button onClick={() => setShowCreate(true)}>+ Nuova</Button>} />

      {!data?.length ? (
        <EmptyState icon="📌" title="Nessuna regola" description="Le regole determinano il comportamento degli assistenti." actionLabel="+ Nuova" onAction={() => setShowCreate(true)} />
      ) : (
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {data.map(r => (
            <Card key={r.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600 }}>{r.name}</div>
                <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', marginTop: 2 }}>{r.description}</div>
                <div style={{ marginTop: 6, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  <Badge label={`p${r.priority}`} color="blue" />
                  <Badge label={r.is_active ? 'attiva' : 'disattiva'} color={r.is_active ? 'green' : 'gray'} />
                </div>
                <div style={{ marginTop: 8, fontSize: '0.8125rem', fontFamily: 'monospace', color: 'var(--color-text-muted)' }}>
                  IF {r.condition} → {r.action}
                </div>
              </div>
              <Button size="sm" variant="danger" onClick={() => setDeleteId(r.id)}>Elimina</Button>
            </Card>
          ))}
        </div>
      )}

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Nuova regola"
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowCreate(false)}>Annulla</Button>
            <Button loading={createMut.isPending} onClick={() => createMut.mutate(form)}>Crea</Button>
          </>
        }>
        <FormField label="Nome" required><Input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} /></FormField>
        <FormField label="Condizione"><Input value={form.condition ?? ''} onChange={e => setForm(f => ({ ...f, condition: e.target.value }))} placeholder="intent == 'greeting'" /></FormField>
        <FormField label="Azione"><Input value={form.action ?? ''} onChange={e => setForm(f => ({ ...f, action: e.target.value }))} placeholder="route_to(assistant_id=1)" /></FormField>
        <FormField label="Priorità"><Input type="number" value={form.priority} onChange={e => setForm(f => ({ ...f, priority: Number(e.target.value) }))} /></FormField>
      </Modal>

      <ConfirmDialog open={deleteId !== null} message="Eliminare la regola?" loading={deleteMut.isPending}
        onConfirm={() => deleteId !== null && deleteMut.mutate(deleteId)} onCancel={() => setDeleteId(null)} />
    </div>
  )
}
