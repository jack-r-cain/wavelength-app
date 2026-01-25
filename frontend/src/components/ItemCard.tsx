import { useDeleteItem } from '../hooks/useItems'
import type { Item } from '../types/item'

interface ItemCardProps {
  item: Item
}

export function ItemCard({ item }: ItemCardProps) {
  const deleteMutation = useDeleteItem()

  const handleDelete = () => {
    if (confirm('Delete this item?')) {
      deleteMutation.mutate(item.id)
    }
  }

  return (
    <div className='bg-white rounded-lg shadow p-4'>
      <h3 className='font-bold text-lg'>{item.title}</h3>
      <p className='text-sm text-gray-600'>{item.type}</p>
      {item.creator && <p className='text-sm'>{item.creator}</p>}
      {item.year && <p className='text-sm text-gray-500'>{item.year}</p>}

      <button
        onClick={handleDelete}
        className='mt-2 text-red-600 text-sm hover:text-red-800'>
        Delete
      </button>
    </div>
  )
}
