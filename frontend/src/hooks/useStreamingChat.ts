import { useEffect, useState } from 'react'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export function useStreamingChat(sessionId: string) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)

  useEffect(() => {
    setMessages([])
  }, [sessionId])

  const sendMessage = async (question: string) => {
    setMessages((prev) => [...prev, { role: 'user', content: question }])
    setIsStreaming(true)

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/knowledge/ask/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, session_id: sessionId }),
      })

      if (!response.ok) throw new Error(`Streaming failed with ${response.status}`)
      if (!response.body) throw new Error('No response body')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let assistantMessage = ''
      let updateCounter = 0
      let buffer = ''

      setMessages((prev) => [...prev, { role: 'assistant', content: '' }])

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const events = buffer.split('\n\n')
        buffer = events.pop() ?? ''

        for (const event of events) {
          const line = event
            .split('\n')
            .find((eventLine) => eventLine.startsWith('data: '))
          if (line?.startsWith('data: ')) {
            const payload = JSON.parse(line.slice(6)) as {
              type?: string
              content?: string
            }
            if (payload.type === 'token' && payload.content) {
              assistantMessage += payload.content
              updateCounter++

              if (updateCounter % 3 === 0 || done) {
                setMessages((prev) => [
                  ...prev.slice(0, -1),
                  { role: 'assistant', content: assistantMessage },
                ])
                await new Promise((resolve) => setTimeout(resolve, 10))
              }
            }
          }
        }
      }

      // Final update to ensure complete message
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { role: 'assistant', content: assistantMessage },
      ])
    } catch (error) {
      console.error('Streaming error:', error)
      setMessages((prev) => [
        ...prev.filter((message, index) => {
          if (index !== prev.length - 1) return true
          return message.content.trim().length > 0
        }),
        { role: 'assistant', content: 'The knowledge agent hit an error while streaming.' },
      ])
    } finally {
      setIsStreaming(false)
    }
  }

  return { messages, sendMessage, isStreaming }
}
