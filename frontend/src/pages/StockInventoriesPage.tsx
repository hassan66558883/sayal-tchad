import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { listProducts } from '../api/products'
import { createStockInventory, listStockInventories, listWarehouses, validateStockInventory } from '../api/stock'
import { useAuth } from '../auth/AuthContext'

interface DraftLine {
  product_id: number
  counted_qty: number
}

export default function StockInventoriesPage() {
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const canManage = hasRole('stock')

  const { data: inventories } = useQuery({ queryKey: ['stock-inventories'], queryFn: listStockInventories })
  const { data: products } = useQuery({ queryKey: ['products'], queryFn: listProducts })
  const { data: warehouses } = useQuery({ queryKey: ['warehouses'], queryFn: listWarehouses })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['stock-inventories'] })
    queryClient.invalidateQueries({ queryKey: ['product-stock'] })
  }
  const createMutation = useMutation({ mutationFn: createStockInventory, onSuccess: invalidate })
  const validateMutation = useMutation({ mutationFn: validateStockInventory, onSuccess: invalidate })

  const [warehouseId, setWarehouseId] = useState('')
  const [inventoryDate, setInventoryDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [lines, setLines] = useState<DraftLine[]>([])
  const [lineProductId, setLineProductId] = useState('')
  const [lineQty, setLineQty] = useState('')

  function productName(id: number) {
    return products?.find((p) => p.id === id)?.name ?? id
  }
  function warehouseCode(id: number) {
    return warehouses?.find((w) => w.id === id)?.code ?? id
  }

  function addLine() {
    if (!lineProductId || lineQty === '') return
    setLines((prev) => [...prev, { product_id: Number(lineProductId), counted_qty: Number(lineQty) }])
    setLineProductId('')
    setLineQty('')
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    createMutation.mutate({ warehouse_id: Number(warehouseId), inventory_date: inventoryDate, lines })
    setLines([])
    setWarehouseId('')
  }

  return (
    <div>
      <h1>Inventaires</h1>
      <table className="data-table">
        <thead>
          <tr>
            <th>Reference</th>
            <th>Entrepot</th>
            <th>Date</th>
            <th>Statut</th>
            <th>Lignes (compte / theorique)</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {inventories?.map((inv) => (
            <tr key={inv.id}>
              <td>{inv.reference}</td>
              <td>{warehouseCode(inv.warehouse_id)}</td>
              <td>{inv.inventory_date}</td>
              <td>{inv.state}</td>
              <td>
                {inv.lines
                  .map((l) => `${productName(l.product_id)}: ${l.counted_qty} / ${l.theoretical_qty ?? '?'}`)
                  .join(', ')}
              </td>
              <td>
                {canManage && inv.state === 'draft' && (
                  <button onClick={() => validateMutation.mutate(inv.id)}>Valider</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {canManage && (
        <form className="inline-form" onSubmit={handleSubmit} style={{ maxWidth: 480 }}>
          <h2>Nouvel inventaire</h2>
          <select value={warehouseId} onChange={(e) => setWarehouseId(e.target.value)} required>
            <option value="">Entrepot</option>
            {warehouses?.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
          </select>
          <input type="date" value={inventoryDate} onChange={(e) => setInventoryDate(e.target.value)} required />

          <fieldset className="role-picker">
            <legend>Lignes de comptage</legend>
            {lines.map((l, i) => (
              <div key={i}>
                {productName(l.product_id)} : {l.counted_qty}
              </div>
            ))}
            <select value={lineProductId} onChange={(e) => setLineProductId(e.target.value)}>
              <option value="">Produit</option>
              {products?.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
            <input
              placeholder="Quantite comptee"
              type="number"
              value={lineQty}
              onChange={(e) => setLineQty(e.target.value)}
            />
            <button type="button" onClick={addLine}>
              Ajouter la ligne
            </button>
          </fieldset>

          <button type="submit" disabled={createMutation.isPending}>
            Creer l'inventaire
          </button>
        </form>
      )}
    </div>
  )
}
