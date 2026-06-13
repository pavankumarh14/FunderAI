import type { EvaluateResponse, EvaluateRequest, GrantOpportunityRequest } from './types'

const BASE = '/api'

export async function healthCheck(): Promise<boolean> {
  try { return (await fetch(`${BASE}/health`)).ok } catch { return false }
}

export async function evaluate(payload: EvaluateRequest): Promise<EvaluateResponse> {
  const res = await fetch(`${BASE}/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as { detail?: string }
    throw new Error(err.detail ?? `API error ${res.status}`)
  }
  return res.json()
}

export async function runDemo(): Promise<EvaluateResponse> {
  const res = await fetch(`${BASE}/demo`)
  if (!res.ok) throw new Error(`API error ${res.status}`)
  return res.json()
}

export async function ingestPdf(file: File): Promise<GrantOpportunityRequest> {
  const formData = new FormData()
  formData.append('file', file)
  
  const res = await fetch(`${BASE}/ingest`, {
    method: 'POST',
    body: formData,
  })
  
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as { detail?: string }
    throw new Error(err.detail ?? `API error ${res.status}`)
  }
  
  return res.json()
}
