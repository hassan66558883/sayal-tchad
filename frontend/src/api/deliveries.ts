import { apiClient } from './client'

export interface Vehicle {
  id: number
  name: string
  plate_number: string
  active: boolean
}

export interface Driver {
  id: number
  name: string
  user_id: number | null
  active: boolean
}

export interface DeliveryLine {
  id: number
  product_id: number
  ordered_qty: number
  delivered_qty: number
}

export type DeliveryState = 'planifiee' | 'chargee' | 'en_livraison' | 'livree' | 'partielle' | 'probleme'
export type RouteState = 'planifiee' | 'chargee' | 'en_livraison' | 'livree' | 'cloturee'

export interface Delivery {
  id: number
  reference: string
  route_id: number
  sale_order_id: number
  state: DeliveryState
  signature_data: string | null
  photo_url: string | null
  delivered_at: string | null
  gps_latitude: number | null
  gps_longitude: number | null
  issue_description: string | null
  lines: DeliveryLine[]
}

export interface DeliveryRoute {
  id: number
  reference: string
  driver_id: number
  vehicle_id: number
  warehouse_id: number | null
  route_date: string
  state: RouteState
  deliveries: Delivery[]
}

export const listVehicles = async (): Promise<Vehicle[]> => (await apiClient.get<Vehicle[]>('/vehicles')).data

export const createVehicle = async (input: { name: string; plate_number: string }): Promise<Vehicle> =>
  (await apiClient.post<Vehicle>('/vehicles', input)).data

export const listDrivers = async (): Promise<Driver[]> => (await apiClient.get<Driver[]>('/drivers')).data

export const createDriver = async (input: { name: string; user_id?: number }): Promise<Driver> =>
  (await apiClient.post<Driver>('/drivers', input)).data

export const listDeliveryRoutes = async (): Promise<DeliveryRoute[]> =>
  (await apiClient.get<DeliveryRoute[]>('/delivery-routes')).data

export const createDeliveryRoute = async (input: {
  driver_id: number
  vehicle_id: number
  warehouse_id?: number
  route_date: string
}): Promise<DeliveryRoute> => (await apiClient.post<DeliveryRoute>('/delivery-routes', input)).data

export const loadRoute = async (id: number): Promise<DeliveryRoute> =>
  (await apiClient.post<DeliveryRoute>(`/delivery-routes/${id}/load`)).data

export const startRoute = async (id: number): Promise<DeliveryRoute> =>
  (await apiClient.post<DeliveryRoute>(`/delivery-routes/${id}/start`)).data

export const finishRoute = async (id: number): Promise<DeliveryRoute> =>
  (await apiClient.post<DeliveryRoute>(`/delivery-routes/${id}/finish`)).data

export const closeRoute = async (id: number): Promise<DeliveryRoute> =>
  (await apiClient.post<DeliveryRoute>(`/delivery-routes/${id}/close`)).data

export const listDeliveries = async (): Promise<Delivery[]> =>
  (await apiClient.get<Delivery[]>('/deliveries')).data

export const createDelivery = async (input: { route_id: number; sale_order_id: number }): Promise<Delivery> =>
  (await apiClient.post<Delivery>('/deliveries', input)).data

export const confirmDelivery = async (
  id: number,
  input: {
    lines: { line_id: number; delivered_qty: number }[]
    signature_data?: string
    photo_url?: string
    gps_latitude?: number
    gps_longitude?: number
    issue_description?: string
  },
): Promise<Delivery> => (await apiClient.post<Delivery>(`/deliveries/${id}/confirm`, input)).data
