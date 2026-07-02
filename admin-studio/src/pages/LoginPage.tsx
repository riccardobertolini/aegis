import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/auth.store'
import './LoginPage.css'

const schema = z.object({
  username: z.string().min(1, 'Username required'),
  password: z.string().min(1, 'Password required'),
})
type FormValues = z.infer<typeof schema>

export function LoginPage() {
  const login = useAuthStore((s) => s.login)
  const navigate = useNavigate()

  const { register, handleSubmit, formState: { errors, isSubmitting }, setError } = useForm<FormValues>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormValues) => {
    try {
      await login(data.username, data.password)
      navigate('/dashboard', { replace: true })
    } catch {
      setError('root', { message: 'Invalid credentials' })
    }
  }

  return (
    <div className="login-bg">
      <div className="login-card">
        {/* Logo */}
        <div className="login-logo">
          <svg width="40" height="40" viewBox="0 0 32 32" fill="none" aria-hidden="true">
            <path d="M16 2 L28 8 L28 16 C28 22.627 22.627 28 16 28 C9.373 28 4 22.627 4 16 L4 8 Z" fill="#01696f"/>
            <path d="M16 8 L22 11 L22 16 C22 19.314 19.314 22 16 22 C12.686 22 10 19.314 10 16 L10 11 Z" fill="#0f3638"/>
            <circle cx="16" cy="16" r="3" fill="#cedcd8"/>
          </svg>
          <h1 className="login-title">Aegis Admin Studio</h1>
          <p className="login-subtitle">Enterprise AI Platform — Offline</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="login-form" noValidate>
          <div className="form-group">
            <label htmlFor="username" className="form-label">Username</label>
            <input
              id="username"
              className="input"
              type="text"
              autoComplete="username"
              autoFocus
              {...register('username')}
            />
            {errors.username && <span className="form-error">{errors.username.message}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="password" className="form-label">Password</label>
            <input
              id="password"
              className="input"
              type="password"
              autoComplete="current-password"
              {...register('password')}
            />
            {errors.password && <span className="form-error">{errors.password.message}</span>}
          </div>

          {errors.root && (
            <div className="login-error" role="alert">{errors.root.message}</div>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            disabled={isSubmitting}
            style={{ width: '100%', justifyContent: 'center', marginTop: 'var(--space-2)' }}
          >
            {isSubmitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p className="login-footer">
          Air-gapped · No telemetry · All data local
        </p>
      </div>
    </div>
  )
}
