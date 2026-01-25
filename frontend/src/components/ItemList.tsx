import { useItems } from '../hooks/useItems'
import { ItemCard } from './ItemCard'


export function ItemList() {
  const { data: items, isLoading, error } = useItems()

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error loading items</div>

  return (
    <div className='grid grid-cols-3 gap-4'>
      {items?.map((item) => (
        <ItemCard key={item.id} item={item} />
      ))}
    </div>
  )
}
