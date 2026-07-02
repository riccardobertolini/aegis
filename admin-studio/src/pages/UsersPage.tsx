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
import styles from './UsersPage.module.css'

interface User {
  id: string
  username: string
  full_name: string
  email: string
  roles: string[]
  is_active: boolean
  created_at: string
  last_login_at: string | null
}

interface UserForm {
  username: string
  full_name: string
  email: string
  password: string
  roles: string[]
}

const EMPTY_FORM: UserForm = {
  username: '',
  full_name: '',
  email: '',
  password: '',
  roles: [],
}

export function UsersPage() {
  const qc = useQueryClient()
  const addToast = useToastStore((s) => s.addToast)
  const [modalOpen, setModalOpen] = useState(false)
  const [editUser, setEditUser] = useState<User | null>(null)
  const [form, setForm] = useState<UserForm>(EMPTY_FORM)
  const [deleteTarget, setDeleteTarget] = useState<User | null>(null)
  const [search, setSearch] = useState('')

  const { data: users = [], isLoading } = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: () => api.get('/security/users').then((r) => r.data),
  })

  const { data: roles = [] } = useQuery<{ name: string }[]>({
    queryKey: ['roles-list'],
    queryFn: () => api.get('/security/roles').then((r) => r.data),
  })

  const createMutation = useMutation({
    mutationFn: (data: UserForm) => api.post('/security/users', data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] })
      addToast({ type: 'success', message: 'Utente creato' })
      closeModal()
    },
    onError: () => addToast({ type: 'error', message: 'Errore nella creazione utente' }),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<UserForm> }) =>
      api.patch(`/security/users/${id}`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] })
      addToast({ type: 'success', message: 'Utente aggiornato' })
      closeModal()
    },
    onError: () => addToast({ type: 'error', message: 'Errore aggiornamento' }),
  })

  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) =>
      api.patch(`/security/users/${id}`, { is_active: active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/security/users/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] })
      addToast({ type: 'success', message: 'Utente eliminato' })
      setDeleteTarget(null)
    },
    onError: () => addToast({ type: 'error', message: 'Errore eliminazione' }),
  })

  function openCreate() {
    setEditUser(null)
    setForm(EMPTY_FORM)
    setModalOpen(true)
  }

  function openEdit(u: User) {
    setEditUser(u)
    setForm({ username: u.username, full_name: u.full_name, email: u.email, password: '', roles: u.roles })
    setModalOpen(true)
  }

  function closeModal() {
    setModalOpen(false)
    setEditUser(null)
    setForm(EMPTY_FORM)
  }

  function handleSubmit() {
    if (editUser) {
      const { password, ...rest } = form
      updateMutation.mutate({ id: editUser.id, data: password ? form : rest })
    } else {
      createMutation.mutate(form)
    }
  }

  function toggleRole(role: string) {
    setForm((f) => ({
      ...f,
      roles: f.roles.includes(role) ? f.roles.filter((r) => r !== role) : [...f.roles, role],
    }))
  }

  const filtered = users.filter(
    (u) =>
      u.username.toLowerCase().includes(search.toLowerCase()) ||
      u.full_name.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <div className={styles.page}>
      <PageHeader
        title="Utenti"
        subtitle="Gestione account e accessi"
        actions={
          <Button variant="primary" onClick={openCreate}>
            + Nuovo utente
          </Button>
        }
      />

      <div className={styles.toolbar}>
        <Input
          placeholder="Cerca per nome, email o username…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {isLoading ? (
        <Spinner />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon="users"
          title="Nessun utente"
          description="Crea il primo account per iniziare."
          action={{ label: 'Nuovo utente', onClick: openCreate }}
        />
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Username</th>
                <th>Nome completo</th>
                <th>Email</th>
                <th>Ruoli</th>
                <th>Stato</th>
                <th>Ultimo accesso</th>
                <th>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((u) => (
                <tr key={u.id}>
                  <td className={styles.mono}>{u.username}</td>
                  <td>{u.full_name}</td>
                  <td>{u.email}</td>
                  <td>
                    <div className={styles.roles}>
                      {u.roles.map((r) => (
                        <Badge key={r} variant="neutral">{r}</Badge>
                      ))}
                    </div>
                  </td>
                  <td>
                    <Badge variant={u.is_active ? 'success' : 'error'}>
                      {u.is_active ? 'Attivo' : 'Disabilitato'}
                    </Badge>
                  </td>
                  <td className={styles.muted}>
                    {u.last_login_at ? new Date(u.last_login_at).toLocaleString('it-IT') : '—'}
                  </td>
                  <td>
                    <div className={styles.actions}>
                      <Button variant="ghost" size="sm" onClick={() => openEdit(u)}>Modifica</Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleActiveMutation.mutate({ id: u.id, active: !u.is_active })}
                      >
                        {u.is_active ? 'Disabilita' : 'Abilita'}
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => setDeleteTarget(u)}>Elimina</Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal
        open={modalOpen}
        onClose={closeModal}
        title={editUser ? 'Modifica utente' : 'Nuovo utente'}
        footer={
          <>
            <Button variant="ghost" onClick={closeModal}>Annulla</Button>
            <Button
              variant="primary"
              onClick={handleSubmit}
              loading={createMutation.isPending || updateMutation.isPending}
            >
              {editUser ? 'Salva' : 'Crea'}
            </Button>
          </>
        }
      >
        <div className={styles.form}>
          <FormField label="Username" required>
            <Input
              value={form.username}
              onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
              disabled={!!editUser}
            />
          </FormField>
          <FormField label="Nome completo">
            <Input
              value={form.full_name}
              onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
            />
          </FormField>
          <FormField label="Email">
            <Input
              type="email"
              value={form.email}
              onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
            />
          </FormField>
          <FormField label={editUser ? 'Nuova password (lascia vuoto per non cambiare)' : 'Password'} required={!editUser}>
            <Input
              type="password"
              value={form.password}
              onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
            />
          </FormField>
          <FormField label="Ruoli">
            <div className={styles.roleSelect}>
              {roles.map((r) => (
                <label key={r.name} className={styles.roleCheck}>
                  <input
                    type="checkbox"
                    checked={form.roles.includes(r.name)}
                    onChange={() => toggleRole(r.name)}
                  />
                  {r.name}
                </label>
              ))}
            </div>
          </FormField>
        </div>
      </Modal>

      <ConfirmDialog
        open={!!deleteTarget}
        title="Elimina utente"
        message={`Sei sicuro di voler eliminare l'utente "${deleteTarget?.username}"? L'operazione è irreversibile.`}
        confirmLabel="Elimina"
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
        onCancel={() => setDeleteTarget(null)}
        danger
      />
    </div>
  )
}
