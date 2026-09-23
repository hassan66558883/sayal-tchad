import { apiClient } from './client'
import type { Branch } from './types'

export async function listBranches(): Promise<Branch[]> {
  const { data } = await apiClient.get<Branch[]>('/branches')
  return data
}

export interface CreateBranchInput {
  name: string
  code: string
  address?: string
  city?: string
  phone?: string
}

export async function createBranch(input: CreateBranchInput): Promise<Branch> {
  const { data } = await apiClient.post<Branch>('/branches', input)
  return data
}
