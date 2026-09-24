import { apiClient } from './client'

export interface Warehouse {
  id: number
  name: string
  code: string
  active: boolean
}

export interface StockLot {
  id: number
  product_id: number
  lot_number: string
  expiry_date: string | null
}

export interface StockMove {
  id: number
  move_type: 'in' | 'out' | 'transfer' | 'adjustment_in' | 'adjustment_out'
  product_id: number
  qty: number
  source_warehouse_id: number | null
  dest_warehouse_id: number | null
  lot_id: number | null
  state: 'draft' | 'done'
  reason: string | null
  move_date: string
}

export interface StockInventoryLine {
  id: number
  product_id: number
  counted_qty: number
  theoretical_qty: number | null
}

export interface StockInventory {
  id: number
  reference: string
  warehouse_id: number
  inventory_date: string
  state: 'draft' | 'validated'
  lines: StockInventoryLine[]
}

export interface ProductStock {
  product_id: number
  qty_on_hand: number
  qty_in_transit: number
  warehouse_id: number | null
}

export const listWarehouses = async (): Promise<Warehouse[]> =>
  (await apiClient.get<Warehouse[]>('/warehouses')).data

export const createWarehouse = async (input: { name: string; code: string }): Promise<Warehouse> =>
  (await apiClient.post<Warehouse>('/warehouses', input)).data

export const listStockMoves = async (): Promise<StockMove[]> =>
  (await apiClient.get<StockMove[]>('/stock-moves')).data

export interface CreateStockMoveInput {
  move_type: string
  product_id: number
  qty: number
  source_warehouse_id?: number
  dest_warehouse_id?: number
  reason?: string
}

export const createStockMove = async (input: CreateStockMoveInput): Promise<StockMove> =>
  (await apiClient.post<StockMove>('/stock-moves', input)).data

export const validateStockMove = async (id: number): Promise<StockMove> =>
  (await apiClient.post<StockMove>(`/stock-moves/${id}/validate`)).data

export const getProductStock = async (productId: number, warehouseId?: number): Promise<ProductStock> =>
  (
    await apiClient.get<ProductStock>(`/products/${productId}/stock`, {
      params: warehouseId ? { warehouse_id: warehouseId } : undefined,
    })
  ).data

export const listStockInventories = async (): Promise<StockInventory[]> =>
  (await apiClient.get<StockInventory[]>('/stock-inventories')).data

export const createStockInventory = async (input: {
  warehouse_id: number
  inventory_date: string
  lines: { product_id: number; counted_qty: number }[]
}): Promise<StockInventory> => (await apiClient.post<StockInventory>('/stock-inventories', input)).data

export const validateStockInventory = async (id: number): Promise<StockInventory> =>
  (await apiClient.post<StockInventory>(`/stock-inventories/${id}/validate`)).data

export const createReception = async (importId: number, warehouseId: number): Promise<StockMove[]> =>
  (
    await apiClient.post<StockMove[]>(`/imports/${importId}/create-reception`, null, {
      params: { warehouse_id: warehouseId },
    })
  ).data
