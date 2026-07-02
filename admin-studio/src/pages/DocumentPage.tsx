import { useState, useRef } from 'react'
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
import styles from './DocumentPage.module.css'

interface DocumentEntry {
  id: string
  filename: string
  title: string
  mime_type: string
  size_bytes: number
  chunk_count: number
  indexed: boolean
  created_at: string
  collection: string | null
}

function formatBytes(b: number) {
  if (b < 1024) return `${b} B`
  if (b < 1024 ** 2) return `${(b / 1024).toFixed(1)} KB`
  if (b < 1024 ** 3) return `${(b / 1024 ** 2).toFixed(1)} MB`
  return `${(b / 1024 ** 3).toFixed(2)} GB`
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('it-IT', { day: '2-digit', month: 'short', year: 'numeric' })
}

const MIME_LABELS: Record<string, string> = {
  'application/pdf': 'PDF',
  'text/plain': 'TXT',
  'text/markdown': 'MD',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
  'text/html': 'HTML',
}

export function DocumentPage() {
  const qc = useQueryClient()
  const addToast = useToastStore((s) => s.addToast)
  const fileRef = useRef<HTMLInputElement>(null)

  const [uploadOpen, setUploadOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<DocumentEntry | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [uploadTitle, setUploadTitle] = useState('')
  const [uploadCollection, setUploadCollection] = useState('')
  const [uploadFile, setUploadFile] = useState<File | null>(null)

  const { data: documents = [], isLoading } = useQuery<DocumentEntry[]>({
    queryKey: ['documents'],
    queryFn: () => api.get('/documents').then((r) => r.data),
  })

  const uploadMutation = useMutation({
    mutationFn: () => {
      if (!uploadFile) throw new Error('No file')
      const fd = new FormData()
      fd.append('file', uploadFile)
      if (uploadTitle) fd.append('title', uploadTitle)
      if (uploadCollection) fd.append('collection', uploadCollection)
      return api.post('/documents/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['documents'] })
      addToast({ type: 'success', message: 'Documento caricato e accodato per indexing' })
      setUploadOpen(false)
      setUploadFile(null)
      setUploadTitle('')
      setUploadCollection('')
    },
    onError: () => addToast({ type: 'error', message: 'Errore durante il caricamento' }),
  })

  const indexMutation = useMutation({
    mutationFn: (id: string) => api.post(`/documents/${id}/index`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['documents'] }); addToast({ type: 'success', message: 'Indexing avviato' }) },
    onError: () => addToast({ type: 'error', message: 'Errore avvio indexing' }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/documents/${id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['documents'] }); addToast({ type: 'success', message: 'Documento eliminato' }); setDeleteTarget(null) },
    onError: () => addToast({ type: 'error', message: 'Errore eliminazione' }),
  })

  const filtered = documents.filter((d) =>
    !searchQuery ||
    d.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (d.title ?? '').toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className={styles.page}>
      <PageHeader
        title="Documenti"
        subtitle="Carica e indicizza documenti nella knowledge base del modello"
        actions={
          <Button variant="primary" onClick={() => setUploadOpen(true)}>+ Carica documento</Button>
        }
      />

      <div className={styles.toolbar}>
        <Input
          placeholder="Cerca per nome o titolo…"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{ maxWidth: 320 }}
        />
        <span className={styles.count}>{filtered.length} document{filtered.length === 1 ? 'o' : 'i'}</span>
      </div>

      {isLoading ? <Spinner /> : filtered.length === 0 ? (
        <EmptyState
          icon="library"
          title="Nessun documento"
          description="Carica PDF, testo o documenti Markdown per arricchire la knowledge base."
          action={{ label: 'Carica documento', onClick: () => setUploadOpen(true) }}
        />
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Documento</th>
                <th>Tipo</th>
                <th>Dimensione</th>
                <th>Chunks</th>
                <th>Stato</th>
                <th>Caricato</th>
                <th>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((doc) => (
                <tr key={doc.id}>
                  <td>
                    <div className={styles.docName}>{doc.title || doc.filename}</div>
                    {doc.collection && <div className={styles.docMeta}>📁 {doc.collection}</div>}
                  </td>
                  <td><Badge variant="neutral">{MIME_LABELS[doc.mime_type] ?? doc.mime_type}</Badge></td>
                  <td className={styles.muted}>{formatBytes(doc.size_bytes)}</td>
                  <td className={styles.muted}>{doc.chunk_count > 0 ? doc.chunk_count : '—'}</td>
                  <td>
                    <Badge variant={doc.indexed ? 'success' : 'warning'}>
                      {doc.indexed ? 'Indicizzato' : 'In attesa'}
                    </Badge>
                  </td>
                  <td className={styles.muted}>{formatDate(doc.created_at)}</td>
                  <td>
                    <div className={styles.actions}>
                      {!doc.indexed && (
                        <Button variant="ghost" size="sm" onClick={() => indexMutation.mutate(doc.id)}>
                          Indicizza
                        </Button>
                      )}
                      <Button variant="ghost" size="sm" onClick={() => setDeleteTarget(doc)}>
                        Elimina
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        title="Carica documento"
        footer={
          <>
            <Button variant="ghost" onClick={() => setUploadOpen(false)}>Annulla</Button>
            <Button
              variant="primary"
              onClick={() => uploadMutation.mutate()}
              loading={uploadMutation.isPending}
              disabled={!uploadFile}
            >
              Carica
            </Button>
          </>
        }
      >
        <div className={styles.form}>
          <div
            className={`${styles.dropzone} ${uploadFile ? styles.dropzoneActive : ''}`}
            onClick={() => fileRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault()
              const f = e.dataTransfer.files[0]
              if (f) setUploadFile(f)
            }}
          >
            {uploadFile ? (
              <>
                <span className={styles.dropzoneFile}>📄 {uploadFile.name}</span>
                <span className={styles.muted}>{formatBytes(uploadFile.size)}</span>
              </>
            ) : (
              <>
                <span>Trascina qui il file</span>
                <span className={styles.muted}>oppure clicca per selezionare</span>
                <span className={styles.muted}>PDF, TXT, MD, DOCX, HTML</span>
              </>
            )}
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.txt,.md,.docx,.html"
              style={{ display: 'none' }}
              onChange={(e) => { const f = e.target.files?.[0]; if (f) setUploadFile(f) }}
            />
          </div>

          <FormField label="Titolo (opzionale)">
            <Input
              placeholder="Nome descrittivo del documento"
              value={uploadTitle}
              onChange={(e) => setUploadTitle(e.target.value)}
            />
          </FormField>
          <FormField label="Collezione (opzionale)">
            <Input
              placeholder="es. faq, manuale, note-interne"
              value={uploadCollection}
              onChange={(e) => setUploadCollection(e.target.value)}
            />
          </FormField>
        </div>
      </Modal>

      <ConfirmDialog
        open={!!deleteTarget}
        title="Elimina documento"
        message={`Eliminare "${deleteTarget?.title || deleteTarget?.filename}"? Verrà rimosso anche dall'indice vettoriale.`}
        confirmLabel="Elimina"
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
        onCancel={() => setDeleteTarget(null)}
        danger
      />
    </div>
  )
}
