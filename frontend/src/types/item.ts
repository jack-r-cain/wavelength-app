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
export interface ItemUpdate {
  title?: string
  type?: ItemType
  creator?: string | null
  year?: number | null
  notes?: string | null
  image_url?: string | null
}

export interface ItemWithScore extends Item {
  score: number
  semantic_score: number
  lexical_score: number
}

export interface Citation {
  item_id: number
  title: string
  rationale: string | null
}

export interface RetrievedSource {
  item: Item
  citation_label: string
  snippet: string
  retrieval_score: number
  semantic_score: number
  lexical_score: number
}

export interface AskResult {
  route: 'answer' | 'summary' | 'timeline'
  answer: string
  citations: Citation[]
  sources: RetrievedSource[]
  structured_payload?: Record<string, unknown> | null
  response_id?: string | null
}

export interface ConnectionResult {
  explanation: string
  shared_themes: string[]
  citations: Citation[]
  sources: RetrievedSource[]
}
