import { apiClient } from './client'

export interface Notification {
  id: string
  type: string
  severity: 'info' | 'warning' | 'danger'
  title: string
  message: string
  path: string
}

export const listNotifications = async (): Promise<Notification[]> =>
  (await apiClient.get<Notification[]>('/notifications')).data
