import { useEffect, useRef } from 'react'
import { useChat } from './hooks/useChat'
import { Sidebar } from './components/Sidebar'
import { ChatMessage } from './components/ChatMessage'
import { ChatInput } from './components/ChatInput'
import styles from './App.module.css'

function UserIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <circle cx="9" cy="6.5" r="3" stroke="currentColor" strokeWidth="1.2"/>
      <path d="M2 15.5c0-3 3.1-5 7-5s7 2 7 5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  )
}

function BagIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <path d="M3 6.5h12l-1.5 9H4.5L3 6.5Z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round"/>
      <path d="M6.5 6.5V5a2.5 2.5 0 0 1 5 0v1.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  )
}

const WELCOME_HINT = "Good afternoon. I've prepared a selection of artisanal scents based on your preferences. How would you like to proceed today?"

export default function App() {
  const { messages, isStreaming, sendMessage, clearConversation } = useChat()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className={styles.shell}>
      <Sidebar onNewRequest={clearConversation} />

      <main className={styles.main}>
        {/* Header */}
        <header className={styles.header}>
          <h1 className={styles.title}>Cierge</h1>
          <div className={styles.headerActions}>
            <button className={styles.iconBtn} aria-label="Account">
              <UserIcon />
            </button>
            <button className={styles.iconBtn} aria-label="Bag">
              <BagIcon />
            </button>
          </div>
        </header>

        {/* Chat scroll area */}
        <div className={styles.chatArea}>
          <div className={styles.chatInner}>
            {messages.length === 0 ? (
              <div className={styles.emptyState}>
                <p className={styles.emptyHint}>{WELCOME_HINT}</p>
              </div>
            ) : (
              messages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} />
              ))
            )}
            <div ref={bottomRef} />
          </div>
        </div>

        {/* Input */}
        <ChatInput onSend={sendMessage} disabled={isStreaming} />
      </main>
    </div>
  )
}
