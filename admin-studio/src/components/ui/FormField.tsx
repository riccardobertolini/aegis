import React from 'react'

interface Props {
  label: string
  error?: string
  children: React.ReactNode
  required?: boolean
}

export function FormField({ label, error, children, required }: Props) {
  return (
    <div style={{ marginBottom: '1rem' }}>
      <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, marginBottom: '0.35rem', color: 'var(--color-text)' }}>
        {label}{required && <span style={{ color: 'var(--color-error)', marginLeft: 2 }}>*</span>}
      </label>
      {children}
      {error && <p style={{ color: 'var(--color-error)', fontSize: '0.8125rem', margin: '0.25rem 0 0' }}>{error}</p>}
    </div>
  )
}

const inputStyle: React.CSSProperties = {
  width: '100%', padding: '0.5rem 0.75rem',
  background: 'var(--color-surface-offset)',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-md)',
  fontSize: '0.875rem', color: 'var(--color-text)',
  outline: 'none', boxSizing: 'border-box',
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input style={inputStyle} {...props} />
}

export function Textarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea style={{ ...inputStyle, minHeight: 80, resize: 'vertical' }} {...props} />
}

export function Select({ children, ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select style={{ ...inputStyle, cursor: 'pointer' }} {...props}>{children}</select>
}
