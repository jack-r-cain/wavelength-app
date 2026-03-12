import { api } from '../lib/api'
import type { Item, ItemCreate, ItemUpdate, ItemWithScore } from '../types/item'

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

  // PUT /items/{id}
  update: async (id: number, update: ItemUpdate): Promise<Item> => {
    const { data } = await api.put(`/items/${id}`, update)
    return data
  },

  // DELETE /items/{id}
  delete: async (id: number): Promise<void> => {
    await api.delete(`/items/${id}`)
  },

  search: async (query: string, limit?: number): Promise<ItemWithScore[]> => {
    const { data } = await api.get('/items/search', {
      params: { query, limit },
    })
    return data
  },
}
