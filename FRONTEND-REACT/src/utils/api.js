/**
 * utils/api.js
 * Camada de comunicação com o backend (api.py).
 * Todas as URLs usam /api/... que o proxy do Vite redireciona para localhost:5000
 */

const BASE = import.meta.env.VITE_BACKEND_URL || '/api'

/** Verifica se o backend está pronto */
export async function checkHealth() {
  const res = await fetch(`${BASE}/health`, { signal: AbortSignal.timeout(3000) })
  return res // 200 = pronto, 503 = iniciando
}

/** Retorna status detalhado do Assistant */
export async function getStatus() {
  const res = await fetch(`${BASE}/status`, { signal: AbortSignal.timeout(5000) })
  if (!res.ok) throw new Error('Status indisponível')
  return res.json()
}

/** Envia mensagem e retorna resposta da IA */
export async function sendChat(mensagem) {
  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mensagem }),
    signal: AbortSignal.timeout(30_000), // 30s — modelos locais podem ser lentos
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.erro || `HTTP ${res.status}`)
  return data.resposta
}
