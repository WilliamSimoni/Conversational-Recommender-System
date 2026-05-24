import { useCallback, useRef, useState } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { streamChat } from '../api/chat'
import type { Message, ProductCard } from '../types'

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const conversationIdRef = useRef<string | null>(null)

  const sendMessage = useCallback(async (content: string) => {
    if (isStreaming || !content.trim()) return

    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content: content.trim(),
    }

    const assistantId = uuidv4()
    const assistantMessage: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      products: [],
      isStreaming: true,
    }

    setMessages((prev) => [...prev, userMessage, assistantMessage])
    setIsStreaming(true)

    await streamChat({
      message: content.trim(),
      conversationId: conversationIdRef.current,
      onEvent: (event) => {
        switch (event.type) {
          case 'conversation_start':
            conversationIdRef.current = event.conversation_id
            break

          case 'message_chunk':
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, content: m.content + event.content }
                  : m,
              ),
            )
            break

          case 'recommended_item': {
            const product: ProductCard = {
              product_id: event.product_id,
              title: event.title,
              price: event.price,
              in_stock: event.in_stock,
              reason: event.reason,
              affinity: event.affinity,
              link: event.link,
            }
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, products: [...(m.products ?? []), product] }
                  : m,
              ),
            )
            break
          }

          case 'escalation':
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? {
                      ...m,
                      content: m.content + event.message,
                      escalation: {
                        support_phone: event.support_phone,
                        support_email: event.support_email,
                      },
                    }
                  : m,
              ),
            )
            break

          case 'done':
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, isStreaming: false } : m,
              ),
            )
            setIsStreaming(false)
            break
        }
      },
      onError: (err) => {
        console.error('Stream error:', err)
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content:
                    m.content ||
                    'I apologize — an error occurred. Please try again.',
                  isStreaming: false,
                }
              : m,
          ),
        )
        setIsStreaming(false)
      },
    })
  }, [isStreaming])

  const clearConversation = useCallback(() => {
    setMessages([])
    conversationIdRef.current = null
  }, [])

  return { messages, isStreaming, sendMessage, clearConversation }
}
