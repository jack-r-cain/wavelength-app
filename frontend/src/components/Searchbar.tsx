import { useState, useEffect } from 'react'
import { useSearchItems } from '../hooks/useItems'
import { ItemCard } from './ItemCard'

export function Searchbar() {
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')

  // Debounce: wait 300ms after user stops typing
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery)
    }, 300)

    return () => clearTimeout(timer)
  }, [searchQuery])

  const { data: results, isLoading } = useSearchItems(debouncedQuery)

  return (
    <div className='space-y-4'>
      <input
        type='text'
        onChange={(e) => setSearchQuery(e.target.value)}
        value={searchQuery}
        placeholder='Search your influences...'
        className='w-full px-3 py-2 border rounded-lg'
      />

      {isLoading && <p className='text-gray-500'>Searching...</p>}

      {results && results.length === 0 && searchQuery && (
        <p className='text-gray-500'>No results found</p>
      )}

      <div className='grid grid-cols-3 gap-4'>
        {results?.map((item) => (
          <ItemCard key={item.id} item={item} score={item.score} />
        ))}
      </div>
    </div>
  )
}
