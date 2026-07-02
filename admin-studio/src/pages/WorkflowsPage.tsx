import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { workflowsApi, type WorkflowCreate } from '@/lib/api'
import { useToastStore } from '@/store/toast.store'
import { PageHeader } from '@/components/ui/PageHeader'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageSpinner } from '@/components/ui/Spinner'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { Modal } from '@/components/ui/Modal'
import { FormField, Input, Textarea } from '@/components/ui/FormField'

export function WorkflowsPage() {
  const qc = useQueryClient()
  const toast = useToastStore()
  const [showCreate, setShowCreate] = useState(false)
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [form, setForm] = useState<WorkflowCreate>({ name: '', description: '', steps: '[]' })

  const { data, isLoading } = useQuery({ queryKey: ['workflows'], queryFn: () => workflowsApi.list() })

  const createMut = useMutation({
    mutationFn: workflowsApi.create,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['workflows'] }); setShowCreate(false); toast.success('Workflow creato') },
    onError: (e: Error) => toast.error(e.message),
  })

  const toggleMut = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) => workflowsApi.update(id, { is_active } as Partial<WorkflowCreate>),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workflows'] }),
  })

  const deleteMut = useMutation({
    mutationFn: (id: number) => workflowsApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['workflows'] }); setDeleteId(null); toast.success('Eliminato') },
    onError: (e: Error) => toast.error(e.message),
  })

  if (isLoading) return <PageSpinner />

  return (
    <div>
      <PageHeader title="Workflow" subtitle={`${data?.length ?? 0} workflow`}
        actions={<Button onClick={() => setShowCreate(true)}>+ Nuovo</Button>} />

      {!data?.length ? (
        <EmptyState icon="⚡" title="Nessun workflow" description="Crea un workflow multi-step." actionLabel="+ Nuovo" onAction={() => setShowCreate(true)} />
      ) : (
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {data.map(w => (
            <Card key={w.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ fontWeight: 600 }}>{w.name}</div>
                <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', marginTop: 2 }}>{w.description}</div>
                <div style={{ marginTop: 6 }}>
                  <Badge label={w.is_active ? 'attivo' : 'pausa'} color={w.is_active ? 'green' : 'gray'} />
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <Button size="sm" variant="ghost" onClick={() => toggleMut.mutate({ id: w.id, is_active: !w.is_active })}>
                  {w.is_active ? 'Sospendi' : 'Attiva'}
                </Button>
                <Button size="sm" variant="danger" onClick={() => setDeleteId(w.id)}>Elimina</Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Nuovo workflow"
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowCreate(false)}>Annulla</Button>
            <Button loading={createMut.isPending} onClick={() => createMut.mutate(form)}>Crea</Button>
          </>
        }>
        <FormField label="Nome" required><Input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} /></FormField>
        <FormField label="Descrizione"><Input value={form.description ?? ''} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} /></FormField>
        <FormField label="Steps (JSON)">
          <Textarea value={form.steps ?? '[]'} onChange={e => setForm(f => ({ ...f, steps: e.target.value }))} rows={5} style={{ fontFamily: 'monospace', fontSize: '0.8125rem' }} />
        </FormField>
      </Modal>

      <ConfirmDialog open={deleteId !== null} message="Eliminare il workflow?" loading={deleteMut.isPending}
        onConfirm={() => deleteId !== null && deleteMut.mutate(deleteId)} onCancel={() => setDeleteId(null)} />
    </div>
  )
}
