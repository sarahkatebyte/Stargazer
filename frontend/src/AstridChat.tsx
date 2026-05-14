import { useState, useRef, useEffect } from 'react'

type Message = {
  role: 'user' | 'assistant'
  content: string
}

type Props = {}

export default function AstridChat({ }: Props) {
  const [collapsed, setCollapsed] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "Hey! I'm Astrid, your astronomy guide. I can tell you what's in the sky tonight from any address, look up stars and planets, or walk you through today's NASA picture of the day. What do you want to explore?",
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Auto-scroll to latest message — scroll the container, not the page
  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight
    }
  }, [messages])

  async function handleSend() {
    const text = input.trim()
    if (!text || loading) return

    const userMessage: Message = { role: 'user', content: text }
    const updatedMessages = [...messages, userMessage]
    setMessages(updatedMessages)
    setInput('')
    setLoading(true)

    try {
      // Send the full conversation history to the backend.
      // The WHY: Claude is stateless - it doesn't remember previous messages.
      // We send the entire conversation each time so Claude has full context.
      // This is the same pattern as every chat app (ChatGPT, Vellum, etc).
      // The tradeoff: more tokens per request as conversation grows.
      // In production, you'd truncate or summarize older messages.
      const apiMessages = updatedMessages.map(m => ({
        role: m.role,
        content: m.content,
      }))

      const res = await fetch('/api/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: apiMessages }),
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.error || 'Chat request failed')
      }

      const data = await res.json()
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
    } catch (err: any) {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: `Something went wrong: ${err.message}. Try again?` },
      ])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  return (
    <div style={{
      position: 'fixed',
      bottom: '24px',
      right: '24px',
      width: '360px',
      zIndex: 1000,
      background: 'rgba(5, 10, 20, 0.92)',
      backdropFilter: 'blur(12px)',
      border: '1px solid rgba(79, 195, 247, 0.2)',
      borderRadius: '16px',
      boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div
        onClick={() => setCollapsed(c => !c)}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px 16px',
          cursor: 'pointer',
          borderBottom: collapsed ? 'none' : '1px solid rgba(79, 195, 247, 0.12)',
        }}
      >
        <span style={{ color: '#4fc3f7', fontSize: '12px', letterSpacing: '2px', textTransform: 'uppercase' }}>
          ✦ Astrid
        </span>
        <span style={{ color: '#4fc3f7', fontSize: '16px', lineHeight: 1 }}>
          {collapsed ? '▲' : '▼'}
        </span>
      </div>

      {!collapsed && <>
      {/* Message history */}
      <div ref={messagesContainerRef} style={{
        background: 'transparent',
        padding: '16px',
        height: '280px',
        overflowY: 'auto',
        marginBottom: '0',
      }}>
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              marginBottom: '16px',
              textAlign: msg.role === 'user' ? 'right' : 'left',
            }}
          >
            {msg.role === 'assistant' && (
              <span style={{
                fontSize: '11px',
                color: '#4fc3f7',
                display: 'block',
                marginBottom: '4px',
              }}>
                Astrid
              </span>
            )}
            <div style={{
              display: 'inline-block',
              maxWidth: '85%',
              padding: '12px 16px',
              borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
              background: msg.role === 'user' ? '#1a3a5c' : '#0d1b2a',
              color: '#e8f4fd',
              fontSize: '14px',
              lineHeight: '1.6',
              textAlign: 'left',
              whiteSpace: 'pre-wrap',
            }}>
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ marginBottom: '16px' }}>
            <span style={{
              fontSize: '11px',
              color: '#4fc3f7',
              display: 'block',
              marginBottom: '4px',
            }}>
              Astrid
            </span>
            <div style={{
              display: 'inline-block',
              padding: '12px 16px',
              borderRadius: '16px 16px 16px 4px',
              background: '#0d1b2a',
              color: '#4fc3f7',
              fontSize: '14px',
            }}>
              Looking at the sky...
            </div>
          </div>
        )}

      </div>

      {/* Input */}
      <div style={{ display: 'flex', gap: '8px', padding: '12px 16px', borderTop: '1px solid rgba(79,195,247,0.12)' }}>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder="What's in the sky tonight?"
          disabled={loading}
          style={{
            flex: 1,
            padding: '10px 14px',
            background: 'rgba(13, 27, 42, 0.8)',
            border: '1px solid rgba(79,195,247,0.2)',
            borderRadius: '10px',
            color: '#e8f4fd',
            fontSize: '13px',
            outline: 'none',
          }}
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          style={{
            padding: '10px 16px',
            background: loading ? 'rgba(26,58,92,0.8)' : '#4fc3f7',
            color: '#050a0f',
            border: 'none',
            borderRadius: '10px',
            fontSize: '13px',
            fontWeight: '600',
            cursor: loading ? 'wait' : 'pointer',
          }}
        >
          {loading ? '...' : 'Ask'}
        </button>
      </div>
      </>}
    </div>
  )
}
