import type { SSEEvent } from '../types'

const API_BASE = '' // Vite proxy handles /api in dev, Caddy in prod

interface StreamChatOptions {
  message: string
  conversationId: string | null
  onEvent: (event: SSEEvent) => void
  onError: (err: Error) => void
}

export async function streamChat({
  message,
  conversationId,
  onEvent,
  onError,
}: StreamChatOptions): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}/api/v1/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      body: JSON.stringify({
        message: { role: 'user', content: message },
        conversation_id: conversationId,
      }),
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    if (!response.body) {
      throw new Error('Response body is null')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (trimmed.startsWith('data: ')) {
          const jsonStr = trimmed.slice(6)
          if (jsonStr === '[DONE]') continue
          try {
            const event = JSON.parse(jsonStr) as SSEEvent
            onEvent(event)
          } catch {
            // skip malformed lines
          }
        }
      }
    }
  } catch (err) {
    onError(err instanceof Error ? err : new Error(String(err)))
  }
}
