import { useState, type FormEvent } from 'react'
import { useCreateItem } from '../hooks/useItems'
import type { ItemCreate } from '../types/item'

interface AddItemFormProps {
  onSuccess?: () => void
}

export function AddItemForm({ onSuccess }: AddItemFormProps = {}) {
  const createMutation = useCreateItem()
  const [formData, setFormData] = useState<ItemCreate>({
    title: '',
    type: 'album',
    creator: null,
    year: null,
    notes: null,
    image_url: null,
  })

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    createMutation.mutate(formData, {
      onSuccess: () => {
        // Reset form
        setFormData({
          title: '',
          type: 'album',
          creator: null,
          year: null,
          notes: null,
          image_url: null,
        })
        onSuccess?.()
      },
    })
  }

  return (
    <form onSubmit={handleSubmit} className='space-y-4 max-w-md'>
      <div>
        <label htmlFor='title' className='block text-sm font-medium mb-1'>
          Title
        </label>
        <input
          type='text'
          id='title'
          value={formData.title}
          onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          className='w-full px-3 py-2 border rounded-lg'
          required
        />
      </div>
      <div>
        <label htmlFor='type' className='block text-sm font-medium mb-1'>
          Type
        </label>
        <select
          id='type'
          value={formData.type}
          onChange={(e) =>
            setFormData({
              ...formData,
              type: e.target.value as ItemCreate['type'],
            })
          }
          className='w-full px-3 py-2 border rounded-lg bg-white'>
          <option value='album'>Album</option>
          <option value='film'>Film</option>
          <option value='book'>Book</option>
          <option value='person'>Person</option>
          <option value='place'>Place</option>
        </select>
      </div>
      <div>
        <label htmlFor='creator' className='block text-sm font-medium mb-1'>
          Creator
        </label>
        <input
          type='text'
          id='creator'
          value={formData.creator ?? ''}
          onChange={(e) =>
            setFormData({ ...formData, creator: e.target.value })
          }
          className='w-full px-3 py-2 border rounded-lg'
        />
      </div>
      <div>
        <label htmlFor='year' className='block text-sm font-medium mb-1'>
          Year
        </label>
        <input
          type='number'
          id='year'
          value={formData.year ?? ''}
          onChange={(e) =>
            setFormData({
              ...formData,
              year: e.target.value ? Number(e.target.value) : null,
            })
          }
          className='w-full px-3 py-2 border rounded-lg'
        />
      </div>
      <div>
        <label htmlFor='notes' className='block text-sm font-medium mb-1'>
          Notes
        </label>
        <input
          type='text'
          id='notes'
          value={formData.notes ?? ''}
          onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
          className='w-full px-3 py-2 border rounded-lg'
        />
      </div>
      <button
        type='submit'
        className='bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700'>
        Add Item
      </button>
    </form>
  )
}
