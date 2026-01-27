export const ItemType = {
  ALBUM: 'album',
  FILM: 'film',
  BOOK: 'book',
  PERSON: 'person',
  PLACE: 'place',
} as const

export type ItemType = (typeof ItemType)[keyof typeof ItemType]

export interface Item {
  id: number
  title: string
  type: ItemType
  creator: string | null
  year: number | null
  notes: string | null
  image_url: string | null
  created_at: string
  updated_at: string
}

export interface ItemCreate {
  title: string
  type: ItemType
  creator: string | null
  year: number | null
  notes: string | null
  image_url: string | null
}
export interface ItemWithScore extends Item {
  score: number
}
