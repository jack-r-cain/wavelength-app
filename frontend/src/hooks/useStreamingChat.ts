import { useState } from 'react'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export function useStreamingChat(sessionId: string) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)

  const sendMessage = async (question: string) => {
    setMessages((prev) => [...prev, { role: 'user', content: question }])
    setIsStreaming(true)

    try {
      const response = await fetch('http://localhost:8000/items/ask/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, session_id: sessionId }),
      })

      if (!response.body) throw new Error('No response body')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let assistantMessage = ''
      let updateCounter = 0

      setMessages((prev) => [...prev, { role: 'assistant', content: '' }])

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        console.log('Raw chunk size:', value?.length) // Add this
        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const content = line.slice(6)
            if (content.trim()) {
              assistantMessage += content
              updateCounter++

              // Only update UI every 3 chunks OR on last chunk
              if (updateCounter % 3 === 0 || done) {
                setMessages((prev) => [
                  ...prev.slice(0, -1),
                  { role: 'assistant', content: assistantMessage },
                ])
                // Small delay to make animation visible
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
    } finally {
      setIsStreaming(false)
    }
  }

  return { messages, sendMessage, isStreaming }
}
