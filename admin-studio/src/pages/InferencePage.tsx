import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { PageHeader } from '@/components/ui/PageHeader'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { useToastStore } from '@/store/toast.store'
import { api } from '@/lib/api'
import styles from './InferencePage.module.css'

interface ModelInfo {
  id: string
  name: string
  architecture: string
  is_active: boolean
}

interface InferenceResult {
  generated_text: string
  tokens_generated: number
  elapsed_ms: number
  model_id: string
}

const DEFAULTS = {
  prompt: '',
  max_new_tokens: 128,
  temperature: 0.7,
  top_p: 0.95,
  repetition_penalty: 1.1,
}

export function InferencePage() {
  const addToast = useToastStore((s) => s.addToast)
  const [params, setParams] = useState(DEFAULTS)
  const [result, setResult] = useState<InferenceResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [selectedModel, setSelectedModel] = useState<string>('')

  const { data: models = [], isLoading: modelsLoading } = useQuery<ModelInfo[]>({
    queryKey: ['models'],
    queryFn: () => api.get('/models').then((r) => r.data),
    onSuccess: (data) => {
      const active = data.find((m) => m.is_active)
      if (active && !selectedModel) setSelectedModel(active.id)
    },
  })

  async function runInference() {
    if (!params.prompt.trim()) {
      addToast({ type: 'warning', message: 'Inserisci un prompt' })
      return
    }
    setLoading(true)
    setResult(null)
    try {
      const res = await api.post('/inference/generate', {
        model_id: selectedModel || undefined,
        prompt: params.prompt,
        max_new_tokens: params.max_new_tokens,
        temperature: params.temperature,
        top_p: params.top_p,
        repetition_penalty: params.repetition_penalty,
      })
      setResult(res.data)
    } catch {
      addToast({ type: 'error', message: 'Errore durante la generazione' })
    } finally {
      setLoading(false)
    }
  }

  function setParam<K extends keyof typeof DEFAULTS>(key: K, value: (typeof DEFAULTS)[K]) {
    setParams((p) => ({ ...p, [key]: value }))
  }

  return (
    <div className={styles.page}>
      <PageHeader
        title="Inferenza"
        subtitle="Testa la generazione di testo direttamente dal modello attivo"
      />

      <div className={styles.layout}>
        {/* Left: prompt + output */}
        <div className={styles.main}>
          <div className={styles.section}>
            <label className={styles.label}>Prompt</label>
            <textarea
              className={styles.textarea}
              rows={6}
              placeholder="Inserisci il testo di input..."
              value={params.prompt}
              onChange={(e) => setParam('prompt', e.target.value)}
            />
          </div>

          <div className={styles.runBar}>
            {modelsLoading ? <Spinner /> : (
              <select
                className={styles.modelSelect}
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
              >
                <option value="">Modello attivo</option>
                {models.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name} {m.is_active ? '(attivo)' : ''}
                  </option>
                ))}
              </select>
            )}
            <Button variant="primary" onClick={runInference} loading={loading} disabled={loading}>
              ▶ Genera
            </Button>
          </div>

          {loading && (
            <div className={styles.generating}>
              <Spinner />
              <span>Generazione in corso…</span>
            </div>
          )}

          {result && (
            <div className={styles.resultBox}>
              <div className={styles.resultMeta}>
                <Badge variant="success">{result.tokens_generated} token</Badge>
                <Badge variant="neutral">{result.elapsed_ms} ms</Badge>
                <Badge variant="neutral">{result.model_id}</Badge>
              </div>
              <pre className={styles.resultText}>{result.generated_text}</pre>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigator.clipboard.writeText(result.generated_text)
                  .then(() => addToast({ type: 'success', message: 'Copiato negli appunti' }))}
              >
                Copia output
              </Button>
            </div>
          )}

          {!loading && !result && (
            <EmptyState
              icon="bot"
              title="Nessun output ancora"
              description="Inserisci un prompt e premi Genera per avviare l'inferenza."
            />
          )}
        </div>

        {/* Right: parameters */}
        <aside className={styles.sidebar}>
          <div className={styles.paramSection}>
            <h3 className={styles.paramTitle}>Parametri</h3>

            <div className={styles.paramField}>
              <label className={styles.paramLabel}>
                Max new tokens
                <span className={styles.paramValue}>{params.max_new_tokens}</span>
              </label>
              <input
                type="range" min={8} max={2048} step={8}
                value={params.max_new_tokens}
                onChange={(e) => setParam('max_new_tokens', Number(e.target.value))}
                className={styles.range}
              />
            </div>

            <div className={styles.paramField}>
              <label className={styles.paramLabel}>
                Temperature
                <span className={styles.paramValue}>{params.temperature.toFixed(2)}</span>
              </label>
              <input
                type="range" min={0.01} max={2.0} step={0.01}
                value={params.temperature}
                onChange={(e) => setParam('temperature', Number(e.target.value))}
                className={styles.range}
              />
            </div>

            <div className={styles.paramField}>
              <label className={styles.paramLabel}>
                Top-p
                <span className={styles.paramValue}>{params.top_p.toFixed(2)}</span>
              </label>
              <input
                type="range" min={0.01} max={1.0} step={0.01}
                value={params.top_p}
                onChange={(e) => setParam('top_p', Number(e.target.value))}
                className={styles.range}
              />
            </div>

            <div className={styles.paramField}>
              <label className={styles.paramLabel}>
                Repetition penalty
                <span className={styles.paramValue}>{params.repetition_penalty.toFixed(2)}</span>
              </label>
              <input
                type="range" min={1.0} max={2.0} step={0.01}
                value={params.repetition_penalty}
                onChange={(e) => setParam('repetition_penalty', Number(e.target.value))}
                className={styles.range}
              />
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => setParams(DEFAULTS)}
            >
              Reset defaults
            </Button>
          </div>
        </aside>
      </div>
    </div>
  )
}
