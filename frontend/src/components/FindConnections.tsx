import { useState } from 'react'
import { useItems } from '../hooks/useItems'
import { api } from '../lib/api'

interface ConnectionResult {
  explanation: string
}

export function FindConnections() {
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [result, setResult] = useState<ConnectionResult | null>(null)
  const [loading, setLoading] = useState(false)

  const { data: items } = useItems()

  const toggleItem = (id: number) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter((itemId) => itemId !== id))
    } else {
      setSelectedIds([...selectedIds, id])
    }
  }

  const handleSubmit = async () => {
    setLoading(true)

    try {
      const { data } = await api.post<ConnectionResult>('/items/connections', {
        item_ids: selectedIds,
      })
      setResult(data)
    } catch (error) {
      console.error('Error making connection:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className='space-y-4'>
      {/* Item selection checkboxes */}
      <div className='space-y-2'>
        <h3 className='font-bold'>Select items to analyze:</h3>
        {items?.map((item) => (
          <label key={item.id} className='flex items-center gap-2'>
            <input
              type='checkbox'
              checked={selectedIds.includes(item.id)}
              onChange={() => toggleItem(item.id)}
            />
            <span>{item.title}</span>
            {item.creator && (
              <span className='text-sm text-gray-500'>by {item.creator}</span>
            )}
            <span>{item.type}</span>
          </label>
        ))}
      </div>

      {/* Submit button */}
      <button
        onClick={handleSubmit}
        disabled={selectedIds.length < 2 || loading}
        className='bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50'>
        {loading ? 'Finding...' : 'Find Connections'}
      </button>

      {/* Results */}
      {result && (
        <div className='bg-white p-4 rounded-lg shadow'>
          <h3 className='font-bold mb-2'>Connections:</h3>
          <p className='whitespace-pre-wrap'>{result.explanation}</p>
        </div>
      )}
    </div>
  )
}
