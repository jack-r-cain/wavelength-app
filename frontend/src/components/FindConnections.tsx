import { useState } from 'react'
import { useItems } from '../hooks/useItems'
import { api } from '../lib/api'
import type { ConnectionResult } from '../types/item'
import { useUIStore } from '../stores/uiStore'

export function FindConnections() {
  const [result, setResult] = useState<ConnectionResult | null>(null)
  const [loading, setLoading] = useState(false)

  const selectedItemIds = useUIStore((state) => state.selectedItemIds)
  const toggleSelection = useUIStore((state) => state.toggleSelection)
  const clearSelection = useUIStore((state) => state.clearSelection)

  const { data: items } = useItems()

  const handleSubmit = async () => {
    setLoading(true)

    try {
      const { data } = await api.post<ConnectionResult>('/knowledge/connections', {
        item_ids: selectedItemIds,
      })
      setResult(data)
      clearSelection()
    } catch (error) {
      console.error('Error making connection:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className='space-y-4'>
      <div className='space-y-2'>
        <h3 className='font-bold'>Select items to analyze:</h3>
        {items?.map((item) => (
          <label key={item.id} className='flex items-center gap-2'>
            <input
              type='checkbox'
              checked={selectedItemIds.includes(item.id)}
              onChange={() => toggleSelection(item.id)}
            />
            <span>{item.title}</span>
            {item.creator && (
              <span className='text-sm text-gray-500'>by {item.creator}</span>
            )}
            <span>{item.type}</span>
          </label>
        ))}
      </div>

      <button
        onClick={handleSubmit}
        disabled={selectedItemIds.length < 2 || loading}
        className='bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50'>
        {loading ? 'Finding...' : 'Find Connections'}
      </button>

      {result && (
        <div className='bg-white p-4 rounded-lg shadow'>
          <h3 className='font-bold mb-2'>Connections:</h3>
          <p className='whitespace-pre-wrap'>{result.explanation}</p>
          {result.shared_themes.length > 0 && (
            <p className='mt-3 text-sm text-gray-600'>
              Themes: {result.shared_themes.join(', ')}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
