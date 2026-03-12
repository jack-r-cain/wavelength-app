import { useState, type FormEvent } from 'react'
import { useUpdateItem } from '../hooks/useItems'
import type { Item, ItemUpdate } from '../types/item'

interface EditItemFormProps {
  item: Item
  onSuccess?: () => void
}

export function EditItemForm({ item, onSuccess }: EditItemFormProps) {
  const updateMutation = useUpdateItem()
  const [formData, setFormData] = useState<ItemUpdate>({
    title: item.title,
    type: item.type,
    creator: item.creator,
    year: item.year,
    notes: item.notes,
    image_url: item.image_url,
  })

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    updateMutation.mutate(
      { id: item.id, update: formData },
      { onSuccess: () => onSuccess?.() },
    )
  }

  return (
    <form onSubmit={handleSubmit} className='space-y-4 max-w-md'>
      <div>
        <label htmlFor='edit-title' className='block text-sm font-medium mb-1'>
          Title
        </label>
        <input
          type='text'
          id='edit-title'
          value={formData.title ?? ''}
          onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          className='w-full px-3 py-2 border rounded-lg'
          required
        />
      </div>

      <div>
        <label htmlFor='edit-type' className='block text-sm font-medium mb-1'>
          Type
        </label>
        <select
          id='edit-type'
          value={formData.type}
          onChange={(e) =>
            setFormData({ ...formData, type: e.target.value as Item['type'] })
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
        <label
          htmlFor='edit-creator'
          className='block text-sm font-medium mb-1'>
          Creator
        </label>
        <input
          type='text'
          id='edit-creator'
          value={formData.creator ?? ''}
          onChange={(e) =>
            setFormData({ ...formData, creator: e.target.value || null })
          }
          className='w-full px-3 py-2 border rounded-lg'
        />
      </div>

      <div>
        <label htmlFor='edit-year' className='block text-sm font-medium mb-1'>
          Year
        </label>
        <input
          type='number'
          id='edit-year'
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
        <label htmlFor='edit-notes' className='block text-sm font-medium mb-1'>
          Notes
        </label>
        <input
          type='text'
          id='edit-notes'
          value={formData.notes ?? ''}
          onChange={(e) =>
            setFormData({ ...formData, notes: e.target.value || null })
          }
          className='w-full px-3 py-2 border rounded-lg'
        />
      </div>

      <button
        type='submit'
        disabled={updateMutation.isPending}
        className='bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50'>
        {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
      </button>
    </form>
  )
}
