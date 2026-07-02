import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { categoriesApi, type CategoryCreate } from '@/lib/api'
import { useToastStore } from '@/store/toast.store'
import { PageHeader } from '@/components/ui/PageHeader'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageSpinner } from '@/components/ui/Spinner'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { Modal } from '@/components/ui/Modal'
import { FormField, Input } from '@/components/ui/FormField'

export function CategoriesPage() {
  const qc = useQueryClient()
  const toast = useToastStore()
  const [showCreate, setShowCreate] = useState(false)
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [form, setForm] = useState<CategoryCreate>({ name: '', slug: '', description: '' })

  const { data, isLoading } = useQuery({ queryKey: ['categories'], queryFn: categoriesApi.list })

  const createMut = useMutation({
    mutationFn: categoriesApi.create,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['categories'] }); setShowCreate(false); toast.success('Categoria creata') },
    onError: (e: Error) => toast.error(e.message),
  })

  const deleteMut = useMutation({
    mutationFn: (id: number) => categoriesApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['categories'] }); setDeleteId(null); toast.success('Eliminata') },
    onError: (e: Error) => toast.error(e.message),
  })

  const autoSlug = (name: string) => name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')

  if (isLoading) return <PageSpinner />

  return (
    <div>
      <PageHeader title="Categorie" subtitle={`${data?.length ?? 0} categorie`}
        actions={<Button onClick={() => setShowCreate(true)}>+ Nuova</Button>} />

      {!data?.length ? (
        <EmptyState icon="🏷️" title="Nessuna categoria" description="Organizza i tuoi contenuti con le categorie." actionLabel="+ Nuova" onAction={() => setShowCreate(true)} />
      ) : (
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {data.map(c => (
            <Card key={c.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 600 }}>{c.name}</div>
                <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', fontFamily: 'monospace' }}>/{c.slug}</div>
                {c.description && <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', marginTop: 2 }}>{c.description}</div>}
              </div>
              <Button size="sm" variant="danger" onClick={() => setDeleteId(c.id)}>Elimina</Button>
            </Card>
          ))}
        </div>
      )}

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Nuova categoria"
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowCreate(false)}>Annulla</Button>
            <Button loading={createMut.isPending} onClick={() => createMut.mutate(form)}>Crea</Button>
          </>
        }>
        <FormField label="Nome" required>
          <Input value={form.name} onChange={e => { const n = e.target.value; setForm(f => ({ ...f, name: n, slug: autoSlug(n) })) }} />
        </FormField>
        <FormField label="Slug"><Input value={form.slug} onChange={e => setForm(f => ({ ...f, slug: e.target.value }))} /></FormField>
        <FormField label="Descrizione"><Input value={form.description ?? ''} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} /></FormField>
      </Modal>

      <ConfirmDialog open={deleteId !== null} message="Eliminare la categoria?" loading={deleteMut.isPending}
        onConfirm={() => deleteId !== null && deleteMut.mutate(deleteId)} onCancel={() => setDeleteId(null)} />
    </div>
  )
}
