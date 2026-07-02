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
import styles from './ModelsPage.module.css'

interface ModelEntry {
  id: string
  name: string
  path: string
  architecture: string
  size_bytes: number
  is_active: boolean
  hash_verified: boolean
  registered_at: string
  description: string
}

interface ModelForm {
  name: string
  path: string
  architecture: string
  description: string
}

const EMPTY_FORM: ModelForm = { name: '', path: '', architecture: 'mamba', description: '' }

function formatBytes(b: number) {
  if (b < 1024) return `${b} B`
  if (b < 1024 ** 2) return `${(b / 1024).toFixed(1)} KB`
  if (b < 1024 ** 3) return `${(b / 1024 ** 2).toFixed(1)} MB`
  return `${(b / 1024 ** 3).toFixed(2)} GB`
}

export function ModelsPage() {
  const qc = useQueryClient()
  const addToast = useToastStore((s) => s.addToast)
  const [modalOpen, setModalOpen] = useState(false)
  const [verifyTarget, setVerifyTarget] = useState<string | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<ModelEntry | null>(null)

  const [form, setForm] = useState<ModelForm>(EMPTY_FORM)

  const { data: models = [], isLoading } = useQuery<ModelEntry[]>({
    queryKey: ['models'],
    queryFn: () => api.get('/models').then((r) => r.data),
  })

  const registerMutation = useMutation({
    mutationFn: (data: ModelForm) => api.post('/models', data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['models'] }); addToast({ type: 'success', message: 'Modello registrato' }); setModalOpen(false); setForm(EMPTY_FORM) },
    onError: () => addToast({ type: 'error', message: 'Errore registrazione modello' }),
  })

  const verifyMutation = useMutation({
    mutationFn: (id: string) => api.post(`/models/${id}/verify`),
    onSuccess: (_, id) => { qc.invalidateQueries({ queryKey: ['models'] }); addToast({ type: 'success', message: 'Integrità verificata' }); setVerifyTarget(null) },
    onError: () => addToast({ type: 'error', message: 'Verifica fallita: hash non corrispondente' }),
  })

  const setActiveMutation = useMutation({
    mutationFn: (id: string) => api.post(`/models/${id}/activate`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['models'] }); addToast({ type: 'success', message: 'Modello attivato' }) },
    onError: () => addToast({ type: 'error', message: 'Errore attivazione' }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/models/${id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['models'] }); addToast({ type: 'success', message: 'Modello rimosso' }); setDeleteTarget(null) },
    onError: () => addToast({ type: 'error', message: 'Errore eliminazione' }),
  })

  return (
    <div className={styles.page}>
      <PageHeader
        title="Modelli SSM"
        subtitle="Gestione e integrità dei modelli Mamba / State Space"
        actions={<Button variant="primary" onClick={() => setModalOpen(true)}>+ Registra modello</Button>}
      />

      {isLoading ? <Spinner /> : models.length === 0 ? (
        <EmptyState icon="cpu" title="Nessun modello registrato" description="Copia i file del modello in models/ e registrali qui." action={{ label: 'Registra modello', onClick: () => setModalOpen(true) }} />
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Nome</th>
                <th>Architettura</th>
                <th>Percorso</th>
                <th>Dimensione</th>
                <th>Integrità</th>
                <th>Stato</th>
                <th>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {models.map((m) => (
                <tr key={m.id}>
                  <td>
                    <div className={styles.modelName}>{m.name}</div>
                    {m.description && <div className={styles.modelDesc}>{m.description}</div>}
                  </td>
                  <td><Badge variant="neutral">{m.architecture}</Badge></td>
                  <td className={styles.path}>{m.path}</td>
                  <td className={styles.muted}>{formatBytes(m.size_bytes)}</td>
                  <td><Badge variant={m.hash_verified ? 'success' : 'warning'}>{m.hash_verified ? 'Verificato' : 'Non verificato'}</Badge></td>
                  <td><Badge variant={m.is_active ? 'success' : 'neutral'}>{m.is_active ? 'Attivo' : 'Inattivo'}</Badge></td>
                  <td>
                    <div className={styles.actions}>
                      {!m.is_active && <Button variant="ghost" size="sm" onClick={() => setActiveMutation.mutate(m.id)}>Attiva</Button>}
                      <Button variant="ghost" size="sm" onClick={() => setVerifyTarget(m.id)}>Verifica</Button>
                      <Button variant="ghost" size="sm" onClick={() => setDeleteTarget(m)}>Rimuovi</Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Registra modello"
        footer={
          <>
            <Button variant="ghost" onClick={() => setModalOpen(false)}>Annulla</Button>
            <Button variant="primary" onClick={() => registerMutation.mutate(form)} loading={registerMutation.isPending}>Registra</Button>
          </>
        }
      >
        <div className={styles.form}>
          <FormField label="Nome" required>
            <Input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
          </FormField>
          <FormField label="Percorso file" required>
            <Input placeholder="models/my-model.pt" value={form.path} onChange={(e) => setForm((f) => ({ ...f, path: e.target.value }))} />
          </FormField>
          <FormField label="Architettura">
            <select className={styles.select} value={form.architecture} onChange={(e) => setForm((f) => ({ ...f, architecture: e.target.value }))}>
              <option value="mamba">Mamba (SSM)</option>
              <option value="mamba-minimal">Mamba Minimal (CPU)</option>
              <option value="s4">S4</option>
              <option value="s6">S6</option>
              <option value="other-ssm">Other SSM</option>
            </select>
          </FormField>
          <FormField label="Descrizione">
            <Input value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} />
          </FormField>
        </div>
      </Modal>

      <ConfirmDialog
        open={!!verifyTarget}
        title="Verifica integrità"
        message="Ricalcola e confronta lo SHA-256 del file del modello con il valore registrato. L'operazione può richiedere qualche secondo per file di grandi dimensioni."
        confirmLabel="Verifica ora"
        onConfirm={() => verifyTarget && verifyMutation.mutate(verifyTarget)}
        onCancel={() => setVerifyTarget(null)}
      />

      <ConfirmDialog
        open={!!deleteTarget}
        title="Rimuovi modello"
        message={`Rimuovere la registrazione di "${deleteTarget?.name}"? Il file NON verrà eliminato dal disco.`}
        confirmLabel="Rimuovi"
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
        onCancel={() => setDeleteTarget(null)}
        danger
      />
    </div>
  )
}
