import { apiClient } from './client'
import type { PaymentMethod } from './finance'

export interface Employee {
  id: number
  name: string
  user_id: number | null
  branch_id: number | null
  position: string
  hire_date: string
  base_salary: number
  active: boolean
}

export const listEmployees = async (): Promise<Employee[]> => (await apiClient.get<Employee[]>('/employees')).data

export const createEmployee = async (input: {
  name: string
  user_id?: number
  branch_id?: number
  position: string
  hire_date: string
  base_salary: number
}): Promise<Employee> => (await apiClient.post<Employee>('/employees', input)).data

export type LeaveType = 'conge_paye' | 'maladie' | 'autre'

export interface LeaveRequest {
  id: number
  employee_id: number
  leave_type: LeaveType
  start_date: string
  end_date: string
  reason: string | null
  state: 'en_attente' | 'approuvee' | 'refusee'
}

export const listLeaveRequests = async (): Promise<LeaveRequest[]> =>
  (await apiClient.get<LeaveRequest[]>('/leave-requests')).data

export const createLeaveRequest = async (input: {
  employee_id: number
  leave_type?: LeaveType
  start_date: string
  end_date: string
  reason?: string
}): Promise<LeaveRequest> => (await apiClient.post<LeaveRequest>('/leave-requests', input)).data

export const approveLeaveRequest = async (id: number): Promise<LeaveRequest> =>
  (await apiClient.post<LeaveRequest>(`/leave-requests/${id}/approve`)).data

export const rejectLeaveRequest = async (id: number): Promise<LeaveRequest> =>
  (await apiClient.post<LeaveRequest>(`/leave-requests/${id}/reject`)).data

export interface Payslip {
  id: number
  reference: string
  employee_id: number
  period_start: string
  period_end: string
  base_salary: number
  bonuses: number
  deductions: number
  net_pay: number
  state: 'draft' | 'validated'
  payment_method: PaymentMethod
  cash_session_id: number | null
  bank_account_id: number | null
}

export const listPayslips = async (): Promise<Payslip[]> => (await apiClient.get<Payslip[]>('/payslips')).data

export const createPayslip = async (input: {
  employee_id: number
  period_start: string
  period_end: string
  base_salary: number
  bonuses?: number
  deductions?: number
  payment_method: PaymentMethod
  cash_session_id?: number
  bank_account_id?: number
}): Promise<Payslip> => (await apiClient.post<Payslip>('/payslips', input)).data

export const validatePayslip = async (id: number): Promise<Payslip> =>
  (await apiClient.post<Payslip>(`/payslips/${id}/validate`)).data
