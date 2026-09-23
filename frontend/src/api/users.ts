import { apiClient } from './client'
import type { User } from './types'

export async function listUsers(): Promise<User[]> {
  const { data } = await apiClient.get<User[]>('/users')
  return data
}

export interface CreateUserInput {
  name: string
  email: string
  password: string
  role_codes: string[]
}

export async function createUser(input: CreateUserInput): Promise<User> {
  const { data } = await apiClient.post<User>('/users', input)
  return data
}
