import React from 'react'

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost'

interface Props extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: 'sm' | 'md'
  loading?: boolean
}

const styles: Record<Variant, React.CSSProperties> = {
  primary:   { background: 'var(--color-primary)', color: '#fff', border: 'none' },
  secondary: { background: 'var(--color-surface-offset)', color: 'var(--color-text)', border: '1px solid var(--color-border)' },
  danger:    { background: 'var(--color-error)', color: '#fff', border: 'none' },
  ghost:     { background: 'transparent', color: 'var(--color-text-muted)', border: '1px solid var(--color-border)' },
}

export function Button({ variant = 'primary', size = 'md', loading, children, disabled, style, ...rest }: Props) {
  return (
    <button
      disabled={disabled || loading}
      style={{
        ...styles[variant],
        borderRadius: 'var(--radius-md)',
        padding: size === 'sm' ? '0.35rem 0.75rem' : '0.5rem 1.1rem',
        fontSize: size === 'sm' ? '0.8125rem' : '0.875rem',
        fontWeight: 500,
        cursor: disabled || loading ? 'not-allowed' : 'pointer',
        opacity: disabled || loading ? 0.6 : 1,
        transition: 'opacity 150ms, background 150ms',
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.4rem',
        ...style,
      }}
      {...rest}
    >
      {loading ? '⏳ ' : null}{children}
    </button>
  )
}
