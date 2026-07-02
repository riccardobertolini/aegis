import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { PageHeader } from '@/components/ui/PageHeader'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Modal } from '@/components/ui/Modal'
import { FormField } from '@/components/ui/FormField'
import { Input } from '@/components/ui/Input'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { useToastStore } from '@/store/toast.store'
import { api } from '@/lib/api'
import styles from './KnowledgePage.module.css'

interface KnowledgeBase {
  id: string
  name: string
  description: string
  document_count: number
  chunk_count: number
  embedding_model: string
  created_at: string
  last_indexed_at: string | null
}

interface KbForm {
  name: string
  description: string
  embedding_model: string
}

const EMPTY_FORM: KbForm = { name: '', description: '', embedding_model: 'local-gte' }

export function KnowledgePage() {
  const qc = useQueryClient()
  const addToast = useToastStore((s) => s.addToast)
  const [modalOpen, setModalOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<KnowledgeBase | null>(null)
  const [form, setForm] = useState<KbForm>(EMPTY_FORM)

  const { data: kbs = [], isLoading } = useQuery<KnowledgeBase[]>({
    queryKey: ['knowledge-bases'],
    queryFn: () => api.get('/knowledge/bases').then((r) => r.data),
  })

  const createMutation = useMutation({
    mutationFn: (data: KbForm) => api.post('/knowledge/bases', data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['knowledge-bases'] }); addToast({ type: 'success', message: 'Knowledge base creata' }); setModalOpen(false); setForm(EMPTY_FORM) },
    onError: () => addToast({ type: 'error', message: 'Errore creazione knowledge base' }),
  })

  const reindexMutation = useMutation({
    mutationFn: (id: string) => api.post(`/knowledge/bases/${id}/reindex`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['knowledge-bases'] }); addToast({ type: 'success', message: 'Reindicizzazione avviata' }) },
    onError: () => addToast({ type: 'error', message: 'Errore reindicizzazione' }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/knowledge/bases/${id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['knowledge-bases'] }); addToast({ type: 'success', message: 'Knowledge base eliminata' }); setDeleteTarget(null) },
    onError: () => addToast({ type: 'error', message: 'Errore eliminazione' }),
  })

  return (
    <div className={styles.page}>
      <PageHeader
        title="Knowledge Bases"
        subtitle="Indici vettoriali ChromaDB locali"
        actions={<Button variant="primary" onClick={() => setModalOpen(true)}>+ Nuova knowledge base</Button>}
      />

      {isLoading ? <Spinner /> : kbs.length === 0 ? (
        <EmptyState icon="database" title="Nessuna knowledge base" description="Crea una knowledge base per indicizzare documenti e abilitare la RAG." action={{ label: 'Nuova knowledge base', onClick: () => setModalOpen(true) }} />
      ) : (
        <div className={styles.grid}>
          {kbs.map((kb) => (
            <div key={kb.id} className={styles.card}>
              <div className={styles.cardHeader}>
                <h3 className={styles.kbName}>{kb.name}</h3>
                <Badge variant="neutral">{kb.embedding_model}</Badge>
              </div>
              {kb.description && <p className={styles.kbDesc}>{kb.description}</p>}
              <div className={styles.stats}>
                <div className={styles.stat}><span className={styles.statVal}>{kb.document_count}</span><span className={styles.statLabel}>Documenti</span></div>
                <div className={styles.stat}><span className={styles.statVal}>{kb.chunk_count.toLocaleString()}</span><span className={styles.statLabel}>Chunk</span></div>
                <div className={styles.stat}>
                  <span className={styles.statVal}>{kb.last_indexed_at ? new Date(kb.last_indexed_at).toLocaleDateString('it-IT') : '—'}</span>
                  <span className={styles.statLabel}>Ultimo indice</span>
                </div>
              </div>
              <div className={styles.cardActions}>
                <Button variant="ghost" size="sm" onClick={() => reindexMutation.mutate(kb.id)}>Reindexing</Button>
                <Button variant="ghost" size="sm" onClick={() => setDeleteTarget(kb)}>Elimina</Button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Nuova knowledge base"
        footer={
          <>
            <Button variant="ghost" onClick={() => setModalOpen(false)}>Annulla</Button>
            <Button variant="primary" onClick={() => createMutation.mutate(form)} loading={createMutation.isPending}>Crea</Button>
          </>
        }
      >
        <div className={styles.form}>
          <FormField label="Nome" required><Input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} /></FormField>
          <FormField label="Descrizione"><Input value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} /></FormField>
          <FormField label="Modello embedding">
            <select className={styles.select} value={form.embedding_model} onChange={(e) => setForm((f) => ({ ...f, embedding_model: e.target.value }))}>
              <option value="local-gte">GTE (locale)</option>
              <option value="local-bge">BGE (locale)</option>
              <option value="local-e5">E5 (locale)</option>
            </select>
          </FormField>
        </div>
      </Modal>

      <ConfirmDialog
        open={!!deleteTarget}
        title="Elimina knowledge base"
        message={`Eliminare "${deleteTarget?.name}"? Tutti i chunk e gli indici vettoriali saranno rimossi.`}
        confirmLabel="Elimina"
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
        onCancel={() => setDeleteTarget(null)}
        danger
      />
    </div>
  )
}
