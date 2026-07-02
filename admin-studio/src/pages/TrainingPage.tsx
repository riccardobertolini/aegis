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
import { useToastStore } from '@/store/toast.store'
import { api } from '@/lib/api'
import styles from './TrainingPage.module.css'

type JobStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'

interface TrainingJob {
  id: string
  name: string
  model_id: string
  model_name: string
  status: JobStatus
  progress: number
  current_epoch: number
  total_epochs: number
  loss: number | null
  started_at: string | null
  finished_at: string | null
  created_at: string
  config: Record<string, unknown>
}

interface JobForm {
  name: string
  model_id: string
  total_epochs: number
  learning_rate: string
  batch_size: number
  dataset_path: string
}

const EMPTY_FORM: JobForm = { name: '', model_id: '', total_epochs: 3, learning_rate: '1e-4', batch_size: 8, dataset_path: '' }

const STATUS_VARIANT: Record<JobStatus, 'neutral' | 'warning' | 'success' | 'error'> = {
  queued: 'neutral', running: 'warning', completed: 'success', failed: 'error', cancelled: 'neutral',
}

export function TrainingPage() {
  const qc = useQueryClient()
  const addToast = useToastStore((s) => s.addToast)
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState<JobForm>(EMPTY_FORM)

  const { data: jobs = [], isLoading } = useQuery<TrainingJob[]>({
    queryKey: ['training-jobs'],
    queryFn: () => api.get('/training/jobs').then((r) => r.data),
    refetchInterval: 5000,
  })

  const { data: models = [] } = useQuery<{ id: string; name: string }[]>({
    queryKey: ['models-list'],
    queryFn: () => api.get('/models').then((r) => r.data.map((m: { id: string; name: string }) => ({ id: m.id, name: m.name }))),
  })

  const startMutation = useMutation({
    mutationFn: (data: JobForm) => api.post('/training/jobs', data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['training-jobs'] }); addToast({ type: 'success', message: 'Job avviato' }); setModalOpen(false); setForm(EMPTY_FORM) },
    onError: () => addToast({ type: 'error', message: 'Errore avvio training' }),
  })

  const cancelMutation = useMutation({
    mutationFn: (id: string) => api.post(`/training/jobs/${id}/cancel`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['training-jobs'] }); addToast({ type: 'success', message: 'Job annullato' }) },
    onError: () => addToast({ type: 'error', message: 'Errore annullamento' }),
  })

  return (
    <div className={styles.page}>
      <PageHeader
        title="Training & Fine-tuning"
        subtitle="Gestione job di addestramento SSM locali"
        actions={<Button variant="primary" onClick={() => setModalOpen(true)}>+ Nuovo job</Button>}
      />

      {isLoading ? <Spinner /> : jobs.length === 0 ? (
        <EmptyState icon="zap" title="Nessun job di training" description="Avvia un nuovo job di fine-tuning su un modello SSM locale." action={{ label: 'Nuovo job', onClick: () => setModalOpen(true) }} />
      ) : (
        <div className={styles.list}>
          {jobs.map((job) => (
            <div key={job.id} className={styles.card}>
              <div className={styles.cardTop}>
                <div>
                  <div className={styles.jobName}>{job.name}</div>
                  <div className={styles.jobMeta}>{job.model_name} &mdash; creato {new Date(job.created_at).toLocaleString('it-IT')}</div>
                </div>
                <Badge variant={STATUS_VARIANT[job.status]}>{job.status}</Badge>
              </div>

              {job.status === 'running' && (
                <div className={styles.progressWrap}>
                  <div className={styles.progressBar}>
                    <div className={styles.progressFill} style={{ width: `${job.progress}%` }} />
                  </div>
                  <span className={styles.progressLabel}>
                    Epoch {job.current_epoch}/{job.total_epochs} &mdash; {job.progress.toFixed(1)}%
                    {job.loss !== null && ` — loss: ${job.loss.toFixed(4)}`}
                  </span>
                </div>
              )}

              {job.status === 'completed' && job.loss !== null && (
                <div className={styles.completedMeta}>Loss finale: {job.loss.toFixed(4)} &mdash; completato {job.finished_at ? new Date(job.finished_at).toLocaleString('it-IT') : ''}</div>
              )}

              <div className={styles.cardActions}>
                {job.status === 'running' && (
                  <Button variant="ghost" size="sm" onClick={() => cancelMutation.mutate(job.id)}>Annulla</Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Nuovo job di training"
        footer={
          <>
            <Button variant="ghost" onClick={() => setModalOpen(false)}>Annulla</Button>
            <Button variant="primary" onClick={() => startMutation.mutate(form)} loading={startMutation.isPending}>Avvia</Button>
          </>
        }
      >
        <div className={styles.form}>
          <FormField label="Nome job" required>
            <Input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
          </FormField>
          <FormField label="Modello base" required>
            <select className={styles.select} value={form.model_id} onChange={(e) => setForm((f) => ({ ...f, model_id: e.target.value }))}>
              <option value="">Seleziona modello…</option>
              {models.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
            </select>
          </FormField>
          <FormField label="Dataset (percorso locale)" required>
            <Input placeholder="data/fine-tune.jsonl" value={form.dataset_path} onChange={(e) => setForm((f) => ({ ...f, dataset_path: e.target.value }))} />
          </FormField>
          <div className={styles.row}>
            <FormField label="Epochs">
              <Input type="number" min={1} max={100} value={form.total_epochs} onChange={(e) => setForm((f) => ({ ...f, total_epochs: parseInt(e.target.value) || 1 }))} />
            </FormField>
            <FormField label="Learning rate">
              <Input value={form.learning_rate} onChange={(e) => setForm((f) => ({ ...f, learning_rate: e.target.value }))} />
            </FormField>
            <FormField label="Batch size">
              <Input type="number" min={1} value={form.batch_size} onChange={(e) => setForm((f) => ({ ...f, batch_size: parseInt(e.target.value) || 1 }))} />
            </FormField>
          </div>
        </div>
      </Modal>
    </div>
  )
}
