import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { assistantsApi, type AssistantCreate } from '@/lib/api'
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

export function AssistantsPage() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const toast = useToastStore()
  const [showCreate, setShowCreate] = useState(false)
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [form, setForm] = useState<AssistantCreate>({ name: '', description: '', model_id: '', system_prompt: '' })

  const { data, isLoading } = useQuery({ queryKey: ['assistants'], queryFn: () => assistantsApi.list() })

  const createMut = useMutation({
    mutationFn: assistantsApi.create,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['assistants'] }); setShowCreate(false); toast.success('Assistente creato') },
    onError: (e: Error) => toast.error(e.message),
  })

  const deleteMut = useMutation({
    mutationFn: (id: number) => assistantsApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['assistants'] }); setDeleteId(null); toast.success('Assistente eliminato') },
    onError: (e: Error) => toast.error(e.message),
  })

  const dupMut = useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) => assistantsApi.duplicate(id, name),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['assistants'] }); toast.success('Assistente duplicato') },
    onError: (e: Error) => toast.error(e.message),
  })

  if (isLoading) return <PageSpinner />

  return (
    <div>
      <PageHeader
        title="Assistenti"
        subtitle={`${data?.length ?? 0} assistenti configurati`}
        actions={<Button onClick={() => setShowCreate(true)}>+ Nuovo</Button>}
      />

      {!data?.length ? (
        <EmptyState icon="🤖" title="Nessun assistente" description="Crea il primo assistente AI." actionLabel="+ Nuovo" onAction={() => setShowCreate(true)} />
      ) : (
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {data.map(a => (
            <Card key={a.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
              onClick={() => navigate(`/assistants/${a.id}`)}>
              <div>
                <div style={{ fontWeight: 600 }}>{a.name}</div>
                <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', marginTop: 2 }}>{a.description || 'Nessuna descrizione'}</div>
                <div style={{ marginTop: 6, display: 'flex', gap: 6 }}>
                  <Badge label={a.is_active ? 'attivo' : 'disattivo'} color={a.is_active ? 'green' : 'gray'} />
                  {a.model_id && <Badge label={a.model_id} color="blue" />}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }} onClick={e => e.stopPropagation()}>
                <Button size="sm" variant="ghost" onClick={() => dupMut.mutate({ id: a.id, name: `${a.name} (copia)` })}>Duplica</Button>
                <Button size="sm" variant="danger" onClick={() => setDeleteId(a.id)}>Elimina</Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Nuovo assistente"
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowCreate(false)}>Annulla</Button>
            <Button loading={createMut.isPending} onClick={() => createMut.mutate(form)}>Crea</Button>
          </>
        }>
        <FormField label="Nome" required><Input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="Es. Assistente HR" /></FormField>
        <FormField label="Descrizione"><Input value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} /></FormField>
        <FormField label="Model ID"><Input value={form.model_id} onChange={e => setForm(f => ({ ...f, model_id: e.target.value }))} placeholder="mamba-v1" /></FormField>
        <FormField label="System prompt"><Textarea value={form.system_prompt} onChange={e => setForm(f => ({ ...f, system_prompt: e.target.value }))} rows={4} /></FormField>
      </Modal>

      <ConfirmDialog
        open={deleteId !== null}
        message="Eliminare questo assistente? L'operazione non è reversibile."
        onConfirm={() => deleteId !== null && deleteMut.mutate(deleteId)}
        onCancel={() => setDeleteId(null)}
        loading={deleteMut.isPending}
      />
    </div>
  )
}
