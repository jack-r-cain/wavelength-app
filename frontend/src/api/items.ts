import { api } from '../lib/api'
import type { Item, ItemCreate } from '../types/item'

export const itemsApi = {
  // GET /items
  getAll: async (): Promise<Item[]> => {
    const { data } = await api.get('/items/')
    return data
  },

  // POST /items
  create: async (item: ItemCreate): Promise<Item> => {
    const { data } = await api.post('/items/', item)
    return data
  },

  // DELETE /items/{id}
  delete: async (id: number): Promise<void> => {
    await api.delete(`/items/${id}`)
  },
}
