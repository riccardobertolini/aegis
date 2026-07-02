interface ToggleProps {
  checked: boolean
  onChange: (v: boolean) => void
  label?: string
  disabled?: boolean
  id?: string
}

export function Toggle({ checked, onChange, label, disabled, id }: ToggleProps) {
  const inputId = id ?? `toggle-${Math.random().toString(36).slice(2)}`
  return (
    <label
      style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', cursor: disabled ? 'not-allowed' : 'pointer' }}
    >
      <span className="toggle">
        <input
          type="checkbox"
          id={inputId}
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          disabled={disabled}
        />
        <span className="toggle-track" />
      </span>
      {label && <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text)' }}>{label}</span>}
    </label>
  )
}
