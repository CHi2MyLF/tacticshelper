const API_BASE = '/api'

export async function uploadCSV(file: File): Promise<{
  success: boolean
  squad_id: number
  player_count: number
  message: string
  sample_players: any[]
}> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API_BASE}/import/csv`, { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Upload failed')
  }
  return res.json()
}

export async function getSquads(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/import/squads`)
  return res.json()
}

export async function getPlayers(squadId: number): Promise<any[]> {
  const res = await fetch(`${API_BASE}/squad/${squadId}/players`)
  return res.json()
}

export async function getSquadStats(squadId: number): Promise<any> {
  const res = await fetch(`${API_BASE}/squad/${squadId}/stats`)
  return res.json()
}

export async function getTactics(squadId: number): Promise<any[]> {
  const res = await fetch(`${API_BASE}/tactic/list/${squadId}`)
  return res.json()
}

export async function setConfig(apiKey: string, apiBaseUrl: string, model?: string): Promise<any> {
  const res = await fetch(`${API_BASE}/chat/config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: apiKey, api_base_url: apiBaseUrl, model: model || 'deepseek-chat' }),
  })
  return res.json()
}

export async function getConfigStatus(): Promise<{ has_api_key: boolean; api_base_url: string; model: string }> {
  const res = await fetch(`${API_BASE}/chat/config/status`)
  return res.json()
}

export async function* streamChat(
  message: string,
  squadId: number,
  chatHistory: Array<{ role: string; content: string }>,
  preferences?: Record<string, any>,
): AsyncGenerator<any> {
  const res = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      squad_id: squadId,
      chat_history: chatHistory,
      preferences,
    }),
  })

  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Chat error')
  }

  const reader = res.body?.getReader()
  if (!reader) throw new Error('No response body')

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6).trim()
        if (data) {
          try {
            yield JSON.parse(data)
          } catch {
            // skip malformed JSON
          }
        }
      }
    }
  }
}
