import React from 'react'
import { Modal } from './Modal'
import { Button } from './Button'

interface Props {
  open: boolean
  title?: string
  message: string
  onConfirm: () => void
  onCancel: () => void
  loading?: boolean
}

export function ConfirmDialog({ open, title = 'Conferma', message, onConfirm, onCancel, loading }: Props) {
  return (
    <Modal
      open={open}
      onClose={onCancel}
      title={title}
      footer={
        <>
          <Button variant="ghost" onClick={onCancel} disabled={loading}>Annulla</Button>
          <Button variant="danger" onClick={onConfirm} loading={loading}>Conferma</Button>
        </>
      }
    >
      <p style={{ margin: 0 }}>{message}</p>
    </Modal>
  )
}
