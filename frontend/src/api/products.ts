import { apiClient } from './client'

export interface ProductCategory {
  id: number
  name: string
  code: string
  parent_id: number | null
  active: boolean
}

export interface ProductBrand {
  id: number
  name: string
  code: string
  active: boolean
}

export interface UomCategory {
  id: number
  name: string
}

export interface Uom {
  id: number
  name: string
  category_id: number
  factor: number
  is_reference: boolean
  active: boolean
}

export interface Product {
  id: number
  reference: string
  name: string
  barcode: string | null
  category_id: number | null
  brand_id: number | null
  uom_id: number
  uom_po_id: number | null
  purchase_price: number
  cost_price: number
  sale_price: number
  wholesale_price: number
  retail_price: number
  min_stock_qty: number
  active: boolean
}

export const listProductCategories = async (): Promise<ProductCategory[]> =>
  (await apiClient.get<ProductCategory[]>('/product-categories')).data

export const createProductCategory = async (input: { name: string; code: string }): Promise<ProductCategory> =>
  (await apiClient.post<ProductCategory>('/product-categories', input)).data

export const listProductBrands = async (): Promise<ProductBrand[]> =>
  (await apiClient.get<ProductBrand[]>('/product-brands')).data

export const createProductBrand = async (input: { name: string; code: string }): Promise<ProductBrand> =>
  (await apiClient.post<ProductBrand>('/product-brands', input)).data

export const listUomCategories = async (): Promise<UomCategory[]> =>
  (await apiClient.get<UomCategory[]>('/uom-categories')).data

export const createUomCategory = async (input: { name: string }): Promise<UomCategory> =>
  (await apiClient.post<UomCategory>('/uom-categories', input)).data

export const listUoms = async (): Promise<Uom[]> => (await apiClient.get<Uom[]>('/uoms')).data

export const createUom = async (input: {
  name: string
  category_id: number
  factor: number
  is_reference: boolean
}): Promise<Uom> => (await apiClient.post<Uom>('/uoms', input)).data

export const listProducts = async (): Promise<Product[]> => (await apiClient.get<Product[]>('/products')).data

export interface CreateProductInput {
  name: string
  category_id?: number
  brand_id?: number
  uom_id: number
  sale_price?: number
  cost_price?: number
  min_stock_qty?: number
}

export const createProduct = async (input: CreateProductInput): Promise<Product> =>
  (await apiClient.post<Product>('/products', input)).data
