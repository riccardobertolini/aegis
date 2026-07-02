import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { templatesApi, type TemplateCreate } from '@/lib/api'
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

export function TemplatesPage() {
  const qc = useQueryClient()
  const toast = useToastStore()
  const [showCreate, setShowCreate] = useState(false)
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [form, setForm] = useState<TemplateCreate>({ name: '', description: '', system_prompt: '', default_model_id: '' })

  const { data, isLoading } = useQuery({ queryKey: ['templates'], queryFn: templatesApi.list })

  const createMut = useMutation({
    mutationFn: templatesApi.create,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['templates'] }); setShowCreate(false); toast.success('Template creato') },
    onError: (e: Error) => toast.error(e.message),
  })

  const deleteMut = useMutation({
    mutationFn: (id: number) => templatesApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['templates'] }); setDeleteId(null); toast.success('Eliminato') },
    onError: (e: Error) => toast.error(e.message),
  })

  if (isLoading) return <PageSpinner />

  return (
    <div>
      <PageHeader title="Template" subtitle={`${data?.length ?? 0} template`}
        actions={<Button onClick={() => setShowCreate(true)}>+ Nuovo</Button>} />

      {!data?.length ? (
        <EmptyState icon="📄" title="Nessun template" description="Crea un template riutilizzabile per i tuoi assistenti." actionLabel="+ Nuovo" onAction={() => setShowCreate(true)} />
      ) : (
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {data.map(t => (
            <Card key={t.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ fontWeight: 600 }}>{t.name}</div>
                <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', marginTop: 2 }}>{t.description}</div>
                <div style={{ marginTop: 6, display: 'flex', gap: 6 }}>
                  {t.is_builtin && <Badge label="builtin" color="blue" />}
                  {t.default_model_id && <Badge label={t.default_model_id} color="gray" />}
                </div>
              </div>
              {!t.is_builtin && (
                <Button size="sm" variant="danger" onClick={() => setDeleteId(t.id)}>Elimina</Button>
              )}
            </Card>
          ))}
        </div>
      )}

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Nuovo template"
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowCreate(false)}>Annulla</Button>
            <Button loading={createMut.isPending} onClick={() => createMut.mutate(form)}>Crea</Button>
          </>
        }>
        <FormField label="Nome" required><Input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} /></FormField>
        <FormField label="Descrizione"><Input value={form.description ?? ''} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} /></FormField>
        <FormField label="Model ID default"><Input value={form.default_model_id ?? ''} onChange={e => setForm(f => ({ ...f, default_model_id: e.target.value }))} /></FormField>
        <FormField label="System prompt"><Textarea value={form.system_prompt ?? ''} onChange={e => setForm(f => ({ ...f, system_prompt: e.target.value }))} rows={5} /></FormField>
      </Modal>

      <ConfirmDialog open={deleteId !== null} message="Eliminare il template?" loading={deleteMut.isPending}
        onConfirm={() => deleteId !== null && deleteMut.mutate(deleteId)} onCancel={() => setDeleteId(null)} />
    </div>
  )
}
