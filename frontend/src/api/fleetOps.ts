import { apiClient } from './client'
import type { PaymentMethod } from './finance'

export interface FuelLog {
  id: number
  vehicle_id: number
  driver_id: number | null
  log_date: string
  odometer: number | null
  liters: number
  unit_price: number
  total_cost: number
  payment_method: PaymentMethod
  cash_session_id: number | null
  bank_account_id: number | null
}

export const listFuelLogs = async (vehicleId?: number): Promise<FuelLog[]> =>
  (await apiClient.get<FuelLog[]>('/fuel-logs', { params: vehicleId ? { vehicle_id: vehicleId } : {} })).data

export const createFuelLog = async (input: {
  vehicle_id: number
  driver_id?: number
  log_date: string
  odometer?: number
  liters: number
  unit_price: number
  payment_method: PaymentMethod
  cash_session_id?: number
  bank_account_id?: number
}): Promise<FuelLog> => (await apiClient.post<FuelLog>('/fuel-logs', input)).data

export const getVehicleFuelCost = async (vehicleId: number): Promise<{ total_fuel_cost: number }> =>
  (await apiClient.get<{ total_fuel_cost: number }>(`/vehicles/${vehicleId}/fuel-cost`)).data

export interface VehicleMaintenance {
  id: number
  vehicle_id: number
  maintenance_date: string
  description: string
  cost: number
  state: 'planifiee' | 'terminee' | 'annulee'
  payment_method: PaymentMethod
  cash_session_id: number | null
  bank_account_id: number | null
}

export const listVehicleMaintenances = async (vehicleId?: number): Promise<VehicleMaintenance[]> =>
  (await apiClient.get<VehicleMaintenance[]>('/vehicle-maintenances', { params: vehicleId ? { vehicle_id: vehicleId } : {} })).data

export const createVehicleMaintenance = async (input: {
  vehicle_id: number
  maintenance_date: string
  description: string
  cost: number
  payment_method: PaymentMethod
  cash_session_id?: number
  bank_account_id?: number
}): Promise<VehicleMaintenance> => (await apiClient.post<VehicleMaintenance>('/vehicle-maintenances', input)).data

export const completeVehicleMaintenance = async (id: number): Promise<VehicleMaintenance> =>
  (await apiClient.post<VehicleMaintenance>(`/vehicle-maintenances/${id}/complete`)).data

export const cancelVehicleMaintenance = async (id: number): Promise<VehicleMaintenance> =>
  (await apiClient.post<VehicleMaintenance>(`/vehicle-maintenances/${id}/cancel`)).data

export const getVehicleMaintenanceCost = async (vehicleId: number): Promise<{ total_maintenance_cost: number }> =>
  (await apiClient.get<{ total_maintenance_cost: number }>(`/vehicles/${vehicleId}/maintenance-cost`)).data

export type VehicleDocumentType = 'assurance' | 'controle_technique' | 'vignette' | 'autre'

export interface VehicleDocument {
  id: number
  vehicle_id: number
  document_type: VehicleDocumentType
  reference: string | null
  start_date: string
  end_date: string
  cost: number
}

export const listVehicleDocuments = async (vehicleId?: number): Promise<VehicleDocument[]> =>
  (await apiClient.get<VehicleDocument[]>('/vehicle-documents', { params: vehicleId ? { vehicle_id: vehicleId } : {} })).data

export const listExpiringVehicleDocuments = async (withinDays = 30): Promise<VehicleDocument[]> =>
  (await apiClient.get<VehicleDocument[]>('/vehicle-documents/expiring', { params: { within_days: withinDays } })).data

export const createVehicleDocument = async (input: {
  vehicle_id: number
  document_type: VehicleDocumentType
  reference?: string
  start_date: string
  end_date: string
  cost?: number
}): Promise<VehicleDocument> => (await apiClient.post<VehicleDocument>('/vehicle-documents', input)).data
