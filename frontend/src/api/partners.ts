import { apiClient } from './client'

export interface Partner {
  id: number
  reference: string
  name: string
  is_customer: boolean
  is_supplier: boolean
  customer_type: string | null
  phone: string | null
  email: string | null
  address: string | null
  branch_id: number | null
  salesperson_id: number | null
  credit_limit: number
  active: boolean
}

export const CUSTOMER_TYPES = ['grossiste', 'detaillant', 'supermarche', 'boutique', 'institution'] as const

export async function listPartners(): Promise<Partner[]> {
  const { data } = await apiClient.get<Partner[]>('/partners')
  return data
}

export interface CreatePartnerInput {
  name: string
  is_customer: boolean
  is_supplier: boolean
  customer_type?: string
  phone?: string
  email?: string
  address?: string
  credit_limit?: number
}

export async function createPartner(input: CreatePartnerInput): Promise<Partner> {
  const { data } = await apiClient.post<Partner>('/partners', input)
  return data
}
