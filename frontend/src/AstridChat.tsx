import { useState, useRef, useEffect } from 'react'

type Message = {
  role: 'user' | 'assistant'
  content: string
}

type Props = {}

export default function AstridChat({ }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "Hey! I'm Astrid, your astronomy guide. I can tell you what's in the sky tonight from any address, look up stars and planets, or walk you through today's NASA picture of the day. What do you want to explore?",
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
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
      margin: '32px 0',
      maxWidth: '720px',
      marginLeft: 'auto',
      marginRight: 'auto',
    }}>
      <h2 style={{
        color: '#e8f4fd',
        fontSize: '14px',
        letterSpacing: '2px',
        textTransform: 'uppercase',
        marginBottom: '16px',
      }}>
        Ask Astrid
      </h2>

      {/* Message history */}
      <div style={{
        background: '#080f17',
        border: '1px solid #1a3a5c',
        borderRadius: '16px',
        padding: '20px',
        height: '400px',
        overflowY: 'auto',
        marginBottom: '12px',
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
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={{ display: 'flex', gap: '10px' }}>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder="What's in the sky tonight from Brooklyn?"
          disabled={loading}
          style={{
            flex: 1,
            padding: '14px 18px',
            background: '#0d1b2a',
            border: '1px solid #1a3a5c',
            borderRadius: '12px',
            color: '#e8f4fd',
            fontSize: '14px',
            outline: 'none',
          }}
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          style={{
            padding: '14px 24px',
            background: loading ? '#1a3a5c' : '#4fc3f7',
            color: '#050a0f',
            border: 'none',
            borderRadius: '12px',
            fontSize: '14px',
            fontWeight: '600',
            cursor: loading ? 'wait' : 'pointer',
            letterSpacing: '1px',
          }}
        >
          {loading ? '...' : 'Ask'}
        </button>
      </div>
    </div>
  )
}
