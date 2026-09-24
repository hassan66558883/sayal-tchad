import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { listProducts } from '../api/products'
import { createStockMove, listStockMoves, listWarehouses, validateStockMove } from '../api/stock'
import { useAuth } from '../auth/AuthContext'

const MOVE_TYPES = [
  ['in', 'Entree'],
  ['out', 'Sortie'],
  ['transfer', 'Transfert'],
  ['adjustment_in', 'Ajustement +'],
  ['adjustment_out', 'Ajustement -'],
] as const

const NEEDS_SOURCE = new Set(['out', 'transfer', 'adjustment_out'])
const NEEDS_DEST = new Set(['in', 'transfer', 'adjustment_in'])

export default function StockMovesPage() {
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const canManage = hasRole('stock')

  const { data: moves } = useQuery({ queryKey: ['stock-moves'], queryFn: listStockMoves })
  const { data: products } = useQuery({ queryKey: ['products'], queryFn: listProducts })
  const { data: warehouses } = useQuery({ queryKey: ['warehouses'], queryFn: listWarehouses })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['stock-moves'] })
    queryClient.invalidateQueries({ queryKey: ['product-stock'] })
  }
  const createMutation = useMutation({ mutationFn: createStockMove, onSuccess: invalidate })
  const validateMutation = useMutation({ mutationFn: validateStockMove, onSuccess: invalidate })

  const [moveType, setMoveType] = useState('in')
  const [productId, setProductId] = useState('')
  const [qty, setQty] = useState('')
  const [sourceId, setSourceId] = useState('')
  const [destId, setDestId] = useState('')
  const [error, setError] = useState<string | null>(null)

  function productName(id: number) {
    return products?.find((p) => p.id === id)?.name ?? id
  }
  function warehouseCode(id: number | null) {
    if (id === null) return '-'
    return warehouses?.find((w) => w.id === id)?.code ?? id
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    createMutation.mutate(
      {
        move_type: moveType,
        product_id: Number(productId),
        qty: Number(qty),
        source_warehouse_id: sourceId ? Number(sourceId) : undefined,
        dest_warehouse_id: destId ? Number(destId) : undefined,
      },
      { onError: () => setError('Impossible de creer ce mouvement.'), onSuccess: () => setError(null) },
    )
  }

  return (
    <div>
      <h1>Mouvements de stock</h1>
      <table className="data-table">
        <thead>
          <tr>
            <th>Type</th>
            <th>Produit</th>
            <th>Quantite</th>
            <th>Source</th>
            <th>Destination</th>
            <th>Statut</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {moves?.map((m) => (
            <tr key={m.id}>
              <td>{m.move_type}</td>
              <td>{productName(m.product_id)}</td>
              <td>{m.qty}</td>
              <td>{warehouseCode(m.source_warehouse_id)}</td>
              <td>{warehouseCode(m.dest_warehouse_id)}</td>
              <td>{m.state}</td>
              <td>
                {canManage && m.state === 'draft' && (
                  <button onClick={() => validateMutation.mutate(m.id)}>Valider</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {canManage && (
        <form className="inline-form" onSubmit={handleSubmit}>
          <h2>Nouveau mouvement</h2>
          <select value={moveType} onChange={(e) => setMoveType(e.target.value)}>
            {MOVE_TYPES.map(([code, label]) => (
              <option key={code} value={code}>
                {label}
              </option>
            ))}
          </select>
          <select value={productId} onChange={(e) => setProductId(e.target.value)} required>
            <option value="">Produit</option>
            {products?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <input placeholder="Quantite" type="number" value={qty} onChange={(e) => setQty(e.target.value)} required />
          {NEEDS_SOURCE.has(moveType) && (
            <select value={sourceId} onChange={(e) => setSourceId(e.target.value)} required>
              <option value="">Entrepot source</option>
              {warehouses?.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name}
                </option>
              ))}
            </select>
          )}
          {NEEDS_DEST.has(moveType) && (
            <select value={destId} onChange={(e) => setDestId(e.target.value)} required>
              <option value="">Entrepot destination</option>
              {warehouses?.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name}
                </option>
              ))}
            </select>
          )}
          <button type="submit" disabled={createMutation.isPending}>
            Creer
          </button>
          {error && <p className="error">{error}</p>}
        </form>
      )}
    </div>
  )
}
