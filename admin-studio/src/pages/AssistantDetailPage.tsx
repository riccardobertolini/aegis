import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { assistantsApi } from '@/lib/api'
import { useToastStore } from '@/store/toast.store'
import { PageHeader } from '@/components/ui/PageHeader'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { FormField, Input, Textarea } from '@/components/ui/FormField'
import { PageSpinner } from '@/components/ui/Spinner'
import { Badge } from '@/components/ui/Badge'

export function AssistantDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const toast = useToastStore()

  const { data, isLoading } = useQuery({
    queryKey: ['assistant', id],
    queryFn: () => assistantsApi.get(Number(id)),
    enabled: !!id,
  })

  const [edit, setEdit] = useState<Record<string, string | boolean>>({})

  const updateMut = useMutation({
    mutationFn: (b: Record<string, unknown>) => assistantsApi.update(Number(id), b),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['assistant', id] }); toast.success('Salvato') },
    onError: (e: Error) => toast.error(e.message),
  })

  if (isLoading || !data) return <PageSpinner />

  const merged = { ...data, ...edit }

  return (
    <div>
      <PageHeader
        title={data.name}
        subtitle={`ID: ${data.id}`}
        actions={
          <>
            <Button variant="ghost" onClick={() => navigate('/assistants')}>← Indietro</Button>
            <Button loading={updateMut.isPending} onClick={() => updateMut.mutate(edit)}>Salva</Button>
          </>
        }
      />

      <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: '1fr 1fr' }}>
        <Card>
          <h3 style={{ marginTop: 0, fontSize: '0.9375rem', fontWeight: 600 }}>Configurazione</h3>
          <FormField label="Nome">
            <Input value={merged.name as string} onChange={e => setEdit(p => ({ ...p, name: e.target.value }))} />
          </FormField>
          <FormField label="Descrizione">
            <Input value={merged.description as string} onChange={e => setEdit(p => ({ ...p, description: e.target.value }))} />
          </FormField>
          <FormField label="Model ID">
            <Input value={merged.model_id as string} onChange={e => setEdit(p => ({ ...p, model_id: e.target.value }))} />
          </FormField>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem' }}>
            <label style={{ fontSize: '0.875rem', fontWeight: 500 }}>Attivo</label>
            <input type="checkbox" checked={merged.is_active as boolean}
              onChange={e => setEdit(p => ({ ...p, is_active: e.target.checked }))} />
            <Badge label={merged.is_active ? 'attivo' : 'disattivo'} color={merged.is_active ? 'green' : 'gray'} />
          </div>
        </Card>

        <Card>
          <h3 style={{ marginTop: 0, fontSize: '0.9375rem', fontWeight: 600 }}>System prompt</h3>
          <Textarea
            value={merged.system_prompt as string}
            onChange={e => setEdit(p => ({ ...p, system_prompt: e.target.value }))}
            rows={10}
            style={{ fontFamily: 'monospace', fontSize: '0.8125rem' }}
          />
        </Card>
      </div>
    </div>
  )
}
