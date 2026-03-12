import { useState, useRef, useEffect } from 'react'
import { useStreamingChat } from '../hooks/useStreamingChat'

export function ChatInterface() {
  const [sessionId, setSessionId] = useState(() => crypto.randomUUID())
  const [input, setInput] = useState('')
  const messagesContainerRef = useRef<HTMLDivElement>(null)

  const { messages, sendMessage, isStreaming } = useStreamingChat(sessionId)

  // Scroll the container to bottom when messages update
  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop =
        messagesContainerRef.current.scrollHeight
    }
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isStreaming) return

    await sendMessage(input)
    setInput('')
  }

  const startNewChat = () => {
    setSessionId(crypto.randomUUID())
  }

  return (
    <div className='flex flex-col h-130 bg-white rounded-lg shadow'>
      {/* Header with new chat button */}
      <div className='p-4 border-b flex justify-between items-center'>
        <h3 className='font-bold'>Chat with Wavelength</h3>
        <button
          onClick={startNewChat}
          className='text-sm px-3 py-1 border rounded hover:bg-gray-50'>
          New Chat
        </button>
      </div>

      {/* Messages area */}
      <div
        ref={messagesContainerRef}
        className='flex-1 overflow-y-auto p-4 space-y-4'>
        {messages.map((msg, i) => (
          <div
            key={i}
            className={
              msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'
            }>
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100'
              }`}>
              <p className='whitespace-pre-wrap'>{msg.content}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Input form */}
      <form onSubmit={handleSubmit} className='p-4 border-t'>
        <div className='flex gap-2'>
          <input
            type='text'
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder='Ask about your collection...'
            disabled={isStreaming}
            className='flex-1 px-3 py-2 border rounded-lg disabled:bg-gray-50'
          />
          <button
            type='submit'
            disabled={isStreaming || !input.trim()}
            className='px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed'>
            {isStreaming ? 'Thinking...' : 'Send'}
          </button>
        </div>
      </form>
    </div>
  )
}
