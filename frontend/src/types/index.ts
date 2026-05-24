export interface ConversationStartEvent {
  type: 'conversation_start'
  conversation_id: string
}

export interface MessageChunkEvent {
  type: 'message_chunk'
  content: string
}

export interface RecommendedItemEvent {
  type: 'recommended_item'
  product_id: string
  title: string
  price: number
  in_stock: boolean
  reason: string
  affinity: number
  link: string
}

export interface EscalationEvent {
  type: 'escalation'
  message: string
  support_phone: string
  support_email: string
}

export interface DoneEvent {
  type: 'done'
}

export type SSEEvent =
  | ConversationStartEvent
  | MessageChunkEvent
  | RecommendedItemEvent
  | EscalationEvent
  | DoneEvent

export interface ProductCard {
  product_id: string
  title: string
  price: number
  in_stock: boolean
  reason: string
  affinity: number
  link: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  products?: ProductCard[]
  escalation?: {
    support_phone: string
    support_email: string
  }
  isStreaming?: boolean
}
