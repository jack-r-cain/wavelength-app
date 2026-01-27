import React, { useState } from 'react'
import { api } from '../lib/api'
import type { Item } from '../types/item'

interface AskResult {
  answer: string
  sources: Item[]
}

export function AskQuestion() {
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState<AskResult | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    setLoading(true)

    try {
      const { data } = await api.post<AskResult>('/items/ask', { question })
      setResult(data)
    } catch (error) {
      console.error('Error asking question:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className='space-y-4'>
      <form onSubmit={handleSubmit} className='space-y-2'>
        <input
          type='text'
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder='Ask about your collection...'
          className='w-full px-3 py-2 border rounded-lg'
        />
        <button
          type='submit'
          disabled={loading}
          className='bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700'>
          {loading ? 'Thinking...' : 'Ask'}
        </button>
      </form>

      {result && (
        <div className='space-y-4'>
          <div className='bg-white p-4 rounded-lg shadow'>
            <h3 className='font-bold mb-2'>Answer:</h3>
            <p className='whitespace-pre-wrap'>{result.answer}</p>
          </div>

          {result.sources.length > 0 && (
            <div className='bg-gray-50 p-4 rounded-lg'>
              <h3 className='font-bold mb-2'>Sources:</h3>
              <ul className='space-y-1'>
                {result.sources.map((source) => (
                  <li key={source.id} className='text-sm text-gray-600'>
                    • {source.title} {source.creator && `by ${source.creator}`}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
