import { apiClient } from './client'

export interface PurchaseOrderLine {
  id: number
  product_id: number
  qty: number
  unit_price: number
  subtotal: number
}

export interface PurchaseOrder {
  id: number
  reference: string
  supplier_id: number
  branch_id: number | null
  order_date: string
  state: 'proforma' | 'commande' | 'terminee' | 'annulee'
  amount_total: number
  lines: PurchaseOrderLine[]
}

export interface CreatePurchaseOrderInput {
  supplier_id: number
  order_date: string
  lines: { product_id: number; qty: number; unit_price: number }[]
}

export const listPurchaseOrders = async (): Promise<PurchaseOrder[]> =>
  (await apiClient.get<PurchaseOrder[]>('/purchase-orders')).data

export const createPurchaseOrder = async (input: CreatePurchaseOrderInput): Promise<PurchaseOrder> =>
  (await apiClient.post<PurchaseOrder>('/purchase-orders', input)).data

export const confirmPurchaseOrder = async (id: number): Promise<PurchaseOrder> =>
  (await apiClient.post<PurchaseOrder>(`/purchase-orders/${id}/confirm`)).data

export const terminatePurchaseOrder = async (id: number): Promise<PurchaseOrder> =>
  (await apiClient.post<PurchaseOrder>(`/purchase-orders/${id}/terminate`)).data

export const cancelPurchaseOrder = async (id: number): Promise<PurchaseOrder> =>
  (await apiClient.post<PurchaseOrder>(`/purchase-orders/${id}/cancel`)).data

export interface Container {
  id: number
  number: string
  size: string | null
  notes: string | null
}

export const listContainers = async (): Promise<Container[]> =>
  (await apiClient.get<Container[]>('/containers')).data

export const createContainer = async (input: { number: string; size?: string }): Promise<Container> =>
  (await apiClient.post<Container>('/containers', input)).data

export interface ImportRecord {
  id: number
  reference: string
  purchase_order_id: number
  container_id: number | null
  state: 'nouveau' | 'expedie' | 'arrive' | 'douane' | 'receptionne'
  bl_number: string | null
  port: string | null
  transport_cost: number
  customs_cost: number
  transit_cost: number
  other_costs: number
}

export const listImports = async (): Promise<ImportRecord[]> =>
  (await apiClient.get<ImportRecord[]>('/imports')).data

export const createImport = async (input: {
  purchase_order_id: number
  container_id?: number
}): Promise<ImportRecord> => (await apiClient.post<ImportRecord>('/imports', input)).data

export const updateImportCosts = async (
  id: number,
  input: { transport_cost?: number; customs_cost?: number; transit_cost?: number; other_costs?: number },
): Promise<ImportRecord> => (await apiClient.patch<ImportRecord>(`/imports/${id}`, input)).data

export const advanceImport = async (id: number): Promise<ImportRecord> =>
  (await apiClient.post<ImportRecord>(`/imports/${id}/advance`)).data
