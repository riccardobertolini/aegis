import React from 'react'

type Color = 'green' | 'red' | 'blue' | 'gray' | 'orange'

const palette: Record<Color, { bg: string; color: string }> = {
  green:  { bg: 'var(--color-success-highlight)',      color: 'var(--color-success)' },
  red:    { bg: 'var(--color-error-highlight)',        color: 'var(--color-error)' },
  blue:   { bg: 'var(--color-blue-highlight)',         color: 'var(--color-blue)' },
  gray:   { bg: 'var(--color-surface-offset)',         color: 'var(--color-text-muted)' },
  orange: { bg: 'var(--color-warning-highlight)',      color: 'var(--color-warning)' },
}

export function Badge({ label, color = 'gray' }: { label: string; color?: Color }) {
  const { bg, color: fg } = palette[color]
  return (
    <span style={{
      background: bg, color: fg,
      borderRadius: 'var(--radius-full)',
      padding: '0.15rem 0.6rem',
      fontSize: '0.75rem',
      fontWeight: 600,
      whiteSpace: 'nowrap',
    }}>
      {label}
    </span>
  )
}
