export interface Role {
  id: number
  code: string
  label: string
}

export interface User {
  id: number
  name: string
  email: string
  active: boolean
  is_superuser: boolean
  roles: Role[]
}

export interface Branch {
  id: number
  name: string
  code: string
  address: string | null
  city: string | null
  phone: string | null
  manager_id: number | null
  active: boolean
}

export interface AuditLogEntry {
  id: number
  user_id: number | null
  action: 'create' | 'update' | 'delete'
  model_name: string
  record_id: number
  record_name: string | null
  description: string | null
  created_at: string
}
