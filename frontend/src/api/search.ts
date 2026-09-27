import { apiClient } from './client'

export interface SearchHit {
  id: number
  label: string
  sublabel: string
  path: string
}

export interface SearchResults {
  partners: SearchHit[]
  products: SearchHit[]
  invoices: SearchHit[]
  sale_orders: SearchHit[]
  deliveries: SearchHit[]
}

export const globalSearch = async (q: string): Promise<SearchResults> =>
  (await apiClient.get<SearchResults>('/search', { params: { q } })).data
