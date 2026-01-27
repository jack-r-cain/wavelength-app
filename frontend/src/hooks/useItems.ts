import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { itemsApi } from '../api/items'

export function useItems() {
  return useQuery({
    queryKey: ['items'],
    queryFn: itemsApi.getAll,
  })
}

export function useCreateItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: itemsApi.create,
    onSuccess: () => {
      // Invalidate and refetch items after creating
      queryClient.invalidateQueries({ queryKey: ['items'] })
    },
  })
}

export function useDeleteItem() {
  // Your code here - similar to useCreateItem
  // mutationFn: itemsApi.delete
  // invalidate queries on success
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: itemsApi.delete,
    onSuccess: () => {
      // Invalidate and refetch items after creating
      queryClient.invalidateQueries({ queryKey: ['items'] })
    },
  })
}

export function useSearchItems(query: string, limit: number = 10) {
  return useQuery({
    queryKey: ['items', 'search', query, limit],
    queryFn: () => itemsApi.search(query, limit),
    enabled: query.length > 0, // Only search if query exists
  })
}
