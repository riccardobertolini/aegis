import { useState, useEffect, useRef } from 'react'
import { PageHeader } from '@/components/ui/PageHeader'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { api } from '@/lib/api-client'
import { useToastStore } from '@/store/toast.store'
import styles from './MonitoringPage.module.css'

interface SystemMetrics {
  cpu_percent: number
  memory_used_mb: number
  memory_total_mb: number
  disk_used_gb: number
  disk_total_gb: number
  uptime_seconds: number
  active_sessions: number
  inference_queue_depth: number
  last_inference_ms: number | null
}

function ProgressBar({ value, max, variant = 'default' }: { value: number; max: number; variant?: 'default' | 'warning' | 'error' }) {
  const pct = Math.min(100, (value / max) * 100)
  return (
    <div className={styles.progressTrack}>
      <div
        className={`${styles.progressFill} ${styles[`progress_${variant}`]}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}

function uptime(seconds: number): string {
  const d = Math.floor(seconds / 86400)
  const h = Math.floor((seconds % 86400) / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return [d > 0 && `${d}d`, h > 0 && `${h}h`, `${m}m`].filter(Boolean).join(' ')
}

export function MonitoringPage() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const addToast = useToastStore((s) => s.add)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    load()
  }, [])

  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(load, 10_000)
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current) }
  }, [autoRefresh])

  async function load() {
    try {
      const data = await api.get<SystemMetrics>('/admin/system/metrics')
      setMetrics(data)
    } catch {
      addToast({ type: 'error', message: 'Failed to load system metrics' })
    } finally {
      setLoading(false)
    }
  }

  const cpuVariant = metrics && metrics.cpu_percent > 85 ? 'error' : metrics && metrics.cpu_percent > 60 ? 'warning' : 'default'
  const memPct = metrics ? (metrics.memory_used_mb / metrics.memory_total_mb) * 100 : 0
  const memVariant = memPct > 85 ? 'error' : memPct > 60 ? 'warning' : 'default'
  const diskPct = metrics ? (metrics.disk_used_gb / metrics.disk_total_gb) * 100 : 0
  const diskVariant = diskPct > 85 ? 'error' : diskPct > 60 ? 'warning' : 'default'

  return (
    <div className={styles.page}>
      <PageHeader
        title="System Monitoring"
        description="Real-time local system metrics. No telemetry sent externally."
        actions={
          <div className={styles.headerActions}>
            <Button variant="ghost" size="sm" onClick={load}>Refresh</Button>
            <Button
              variant={autoRefresh ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => setAutoRefresh((v) => !v)}
            >
              {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
            </Button>
          </div>
        }
      />

      {loading ? (
        <div className={styles.center}><Spinner size="lg" /></div>
      ) : metrics ? (
        <div className={styles.grid}>
          <Card className={styles.metricCard}>
            <h3 className={styles.metricTitle}>CPU Usage</h3>
            <p className={styles.metricValue}>{metrics.cpu_percent.toFixed(1)}%</p>
            <ProgressBar value={metrics.cpu_percent} max={100} variant={cpuVariant} />
          </Card>

          <Card className={styles.metricCard}>
            <h3 className={styles.metricTitle}>Memory</h3>
            <p className={styles.metricValue}>
              {metrics.memory_used_mb.toLocaleString()} / {metrics.memory_total_mb.toLocaleString()} MB
            </p>
            <ProgressBar value={metrics.memory_used_mb} max={metrics.memory_total_mb} variant={memVariant} />
          </Card>

          <Card className={styles.metricCard}>
            <h3 className={styles.metricTitle}>Disk</h3>
            <p className={styles.metricValue}>
              {metrics.disk_used_gb.toFixed(1)} / {metrics.disk_total_gb.toFixed(1)} GB
            </p>
            <ProgressBar value={metrics.disk_used_gb} max={metrics.disk_total_gb} variant={diskVariant} />
          </Card>

          <Card className={styles.metricCard}>
            <h3 className={styles.metricTitle}>Uptime</h3>
            <p className={styles.metricValue}>{uptime(metrics.uptime_seconds)}</p>
            <Badge variant="success">Running</Badge>
          </Card>

          <Card className={styles.metricCard}>
            <h3 className={styles.metricTitle}>Active Sessions</h3>
            <p className={styles.metricValue}>{metrics.active_sessions}</p>
          </Card>

          <Card className={styles.metricCard}>
            <h3 className={styles.metricTitle}>Inference Queue</h3>
            <p className={styles.metricValue}>{metrics.inference_queue_depth}</p>
            {metrics.last_inference_ms !== null && (
              <p className={styles.metricSub}>Last: {metrics.last_inference_ms} ms</p>
            )}
          </Card>
        </div>
      ) : null}
    </div>
  )
}
