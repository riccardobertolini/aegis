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
import styles from './RolesPage.module.css'

const ALL_PERMISSIONS = [
  'user:read','user:write','user:delete',
  'role:read','role:write','role:delete',
  'document:read','document:write','document:delete',
  'knowledge:read','knowledge:write',
  'model:read','model:write','model:delete',
  'training:read','training:write',
  'plugin:read','plugin:write',
  'audit:read',
  'backup:create','backup:restore',
  'config:read','config:write',
  'system:read','system:write',
]

interface Role {
  id: string
  name: string
  description: string
  permissions: string[]
  is_system: boolean
  user_count: number
}

interface RoleForm {
  name: string
  description: string
  permissions: string[]
}

const EMPTY_FORM: RoleForm = { name: '', description: '', permissions: [] }

export function RolesPage() {
  const qc = useQueryClient()
  const addToast = useToastStore((s) => s.addToast)
  const [modalOpen, setModalOpen] = useState(false)
  const [editRole, setEditRole] = useState<Role | null>(null)
  const [form, setForm] = useState<RoleForm>(EMPTY_FORM)
  const [deleteTarget, setDeleteTarget] = useState<Role | null>(null)

  const { data: roles = [], isLoading } = useQuery<Role[]>({
    queryKey: ['roles'],
    queryFn: () => api.get('/security/roles').then((r) => r.data),
  })

  const createMutation = useMutation({
    mutationFn: (data: RoleForm) => api.post('/security/roles', data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['roles'] }); addToast({ type: 'success', message: 'Ruolo creato' }); closeModal() },
    onError: () => addToast({ type: 'error', message: 'Errore creazione ruolo' }),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: RoleForm }) => api.put(`/security/roles/${id}`, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['roles'] }); addToast({ type: 'success', message: 'Ruolo aggiornato' }); closeModal() },
    onError: () => addToast({ type: 'error', message: 'Errore aggiornamento' }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/security/roles/${id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['roles'] }); addToast({ type: 'success', message: 'Ruolo eliminato' }); setDeleteTarget(null) },
    onError: () => addToast({ type: 'error', message: 'Errore eliminazione' }),
  })

  function openCreate() { setEditRole(null); setForm(EMPTY_FORM); setModalOpen(true) }
  function openEdit(r: Role) { setEditRole(r); setForm({ name: r.name, description: r.description, permissions: r.permissions }); setModalOpen(true) }
  function closeModal() { setModalOpen(false); setEditRole(null); setForm(EMPTY_FORM) }

  function togglePerm(p: string) {
    setForm((f) => ({ ...f, permissions: f.permissions.includes(p) ? f.permissions.filter((x) => x !== p) : [...f.permissions, p] }))
  }

  function toggleAll() {
    setForm((f) => ({ ...f, permissions: f.permissions.length === ALL_PERMISSIONS.length ? [] : [...ALL_PERMISSIONS] }))
  }

  const grouped = ALL_PERMISSIONS.reduce<Record<string, string[]>>((acc, p) => {
    const [ns] = p.split(':')
    if (!acc[ns]) acc[ns] = []
    acc[ns].push(p)
    return acc
  }, {})

  return (
    <div className={styles.page}>
      <PageHeader
        title="Ruoli & Permessi"
        subtitle="Definisci i livelli di accesso"
        actions={<Button variant="primary" onClick={openCreate}>+ Nuovo ruolo</Button>}
      />

      {isLoading ? <Spinner /> : roles.length === 0 ? (
        <EmptyState icon="shield" title="Nessun ruolo" description="Crea il primo ruolo per definire i permessi." action={{ label: 'Nuovo ruolo', onClick: openCreate }} />
      ) : (
        <div className={styles.grid}>
          {roles.map((role) => (
            <div key={role.id} className={styles.card}>
              <div className={styles.cardHeader}>
                <div>
                  <h3 className={styles.roleName}>{role.name}</h3>
                  {role.description && <p className={styles.roleDesc}>{role.description}</p>}
                </div>
                <div className={styles.cardMeta}>
                  {role.is_system && <Badge variant="warning">Sistema</Badge>}
                  <Badge variant="neutral">{role.user_count} utenti</Badge>
                </div>
              </div>
              <div className={styles.perms}>
                {role.permissions.slice(0, 8).map((p) => (
                  <Badge key={p} variant="neutral" size="sm">{p}</Badge>
                ))}
                {role.permissions.length > 8 && (
                  <Badge variant="neutral" size="sm">+{role.permissions.length - 8}</Badge>
                )}
              </div>
              <div className={styles.cardActions}>
                <Button variant="ghost" size="sm" onClick={() => openEdit(role)} disabled={role.is_system}>Modifica</Button>
                <Button variant="ghost" size="sm" onClick={() => setDeleteTarget(role)} disabled={role.is_system}>Elimina</Button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal
        open={modalOpen}
        onClose={closeModal}
        title={editRole ? 'Modifica ruolo' : 'Nuovo ruolo'}
        size="lg"
        footer={
          <>
            <Button variant="ghost" onClick={closeModal}>Annulla</Button>
            <Button variant="primary" onClick={() => editRole ? updateMutation.mutate({ id: editRole.id, data: form }) : createMutation.mutate(form)} loading={createMutation.isPending || updateMutation.isPending}>
              {editRole ? 'Salva' : 'Crea'}
            </Button>
          </>
        }
      >
        <div className={styles.form}>
          <FormField label="Nome ruolo" required>
            <Input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} disabled={!!editRole} />
          </FormField>
          <FormField label="Descrizione">
            <Input value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} />
          </FormField>
          <FormField label="Permessi">
            <div className={styles.permHeader}>
              <span className={styles.permCount}>{form.permissions.length} / {ALL_PERMISSIONS.length} selezionati</span>
              <Button variant="ghost" size="sm" onClick={toggleAll}>{form.permissions.length === ALL_PERMISSIONS.length ? 'Deseleziona tutti' : 'Seleziona tutti'}</Button>
            </div>
            <div className={styles.permGroups}>
              {Object.entries(grouped).map(([ns, perms]) => (
                <div key={ns} className={styles.permGroup}>
                  <div className={styles.permNs}>{ns}</div>
                  {perms.map((p) => (
                    <label key={p} className={styles.permCheck}>
                      <input type="checkbox" checked={form.permissions.includes(p)} onChange={() => togglePerm(p)} />
                      <span>{p.split(':')[1]}</span>
                    </label>
                  ))}
                </div>
              ))}
            </div>
          </FormField>
        </div>
      </Modal>

      <ConfirmDialog
        open={!!deleteTarget}
        title="Elimina ruolo"
        message={`Eliminare il ruolo "${deleteTarget?.name}"? Gli utenti assegnati perderanno questi permessi.`}
        confirmLabel="Elimina"
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
        onCancel={() => setDeleteTarget(null)}
        danger
      />
    </div>
  )
}
