import { useEffect, useState, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { chatAPI, bugsAPI } from '../services/api'
import ReactMarkdown from 'react-markdown'

export default function ChatPage() {
  const { bugId } = useParams()
  const [bug, setBug] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [loading, setLoading] = useState(true)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    loadData()
  }, [bugId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function loadData() {
    try {
      const [bugRes, historyRes] = await Promise.all([
        bugsAPI.get(bugId),
        chatAPI.history(bugId)
      ])
      setBug(bugRes.data)
      setMessages(historyRes.data.messages || [])
    } catch (err) {
      console.error(err)
    }
    setLoading(false)
  }

  async function handleSend(e) {
    e.preventDefault()
    if (!input.trim() || sending) return

    const userMsg = input.trim()
    setInput('')
    setSending(true)

    // Optimistic update
    setMessages(prev => [...prev, { id: 'temp', role: 'user', content: userMsg }])

    try {
      const { data } = await chatAPI.send(bugId, userMsg)
      setMessages(prev => [
        ...prev.filter(m => m.id !== 'temp'),
        { id: 'user-' + Date.now(), role: 'user', content: userMsg },
        { id: data.message_id || 'ai-' + Date.now(), role: 'assistant', content: data.response }
      ])
    } catch (err) {
      console.error(err)
      setMessages(prev => prev.filter(m => m.id !== 'temp'))
    }
    setSending(false)
  }

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>

  const quickActions = [
    'Explain this bug',
    'How do I fix this?',
    'How can I prevent this?',
    'What\'s the impact?',
  ]

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">💬 Bug Chat</h1>
        {bug && (
          <p className="page-description">
            <span className={`badge badge-${bug.severity}`} style={{marginRight:'8px'}}>{bug.severity}</span>
            {bug.title} — {bug.file_path}
          </p>
        )}
      </div>

      <div className="chat-container">
        <div className="chat-messages">
          {/* Initial context */}
          <div className="chat-message assistant">
            <p style={{marginBottom:'8px'}}>👋 I'm your AI assistant for this bug. I can help you understand:</p>
            <ul style={{paddingLeft:'20px', margin:'8px 0'}}>
              <li><strong>{bug?.title}</strong></li>
              <li>File: <code>{bug?.file_path}</code> (line {bug?.line_number})</li>
              <li>Severity: {bug?.severity}</li>
            </ul>
            <p>Ask me anything about this bug!</p>
          </div>

          {/* Quick actions */}
          {messages.length === 0 && (
            <div style={{display:'flex', gap:'8px', flexWrap:'wrap', justifyContent:'center'}}>
              {quickActions.map(action => (
                <button key={action} className="btn btn-secondary btn-sm" 
                  onClick={() => { setInput(action); }}>
                  {action}
                </button>
              ))}
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={msg.id || i} className={`chat-message ${msg.role}`}>
              {msg.role === 'assistant' ? (
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              ) : (
                msg.content
              )}
            </div>
          ))}

          {sending && (
            <div className="chat-message assistant" style={{opacity:0.6}}>
              <div className="spinner" style={{width:'20px', height:'20px', borderWidth:'2px'}} />
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <form className="chat-input-area" onSubmit={handleSend}>
          <input
            placeholder="Ask about this bug..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={sending}
          />
          <button className="btn btn-primary" disabled={sending || !input.trim()}>
            Send
          </button>
        </form>
      </div>
    </div>
  )
}
