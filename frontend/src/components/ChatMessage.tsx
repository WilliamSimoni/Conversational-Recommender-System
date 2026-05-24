import type { Message } from '../types'
import ReactMarkdown from 'react-markdown'
import { ProductCard } from './ProductCard'
import styles from './ChatMessage.module.css'

interface Props {
  message: Message
}

function SparkleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path
        d="M8 1.5L9.2 6.8L14.5 8L9.2 9.2L8 14.5L6.8 9.2L1.5 8L6.8 6.8L8 1.5Z"
        fill="currentColor"
      />
    </svg>
  )
}

function StreamingCursor() {
  return <span className={styles.cursor} aria-hidden="true" />
}

export function ChatMessage({ message }: Props) {
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div className={styles.userRow}>
        <div className={styles.userBubble}>
          <p className={styles.userText}>{message.content}</p>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.assistantRow}>
      <div className={styles.avatarCol}>
        <div className={styles.avatar}>
          <SparkleIcon />
        </div>
      </div>

      <div className={styles.assistantContent}>
        <div className={styles.assistantBubble}>
          {message.content ? (
            <div className={styles.assistantText}>
              <ReactMarkdown>{message.content}</ReactMarkdown>
              {message.isStreaming && <StreamingCursor />}
            </div>
          ) : message.isStreaming ? (
            <div className={styles.typingIndicator}>
              <span />
              <span />
              <span />
            </div>
          ) : null}
        </div>

        {message.products && message.products.length > 0 && (
          <div className={styles.productsRow}>
            {message.products.map((product, i) => (
              <ProductCard key={product.product_id} product={product} index={i} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
