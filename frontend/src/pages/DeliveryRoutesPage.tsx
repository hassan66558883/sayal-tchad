import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import {
  closeRoute,
  createDelivery,
  createDeliveryRoute,
  finishRoute,
  listDeliveries,
  listDeliveryRoutes,
  listDrivers,
  listVehicles,
  loadRoute,
  startRoute,
} from '../api/deliveries'
import { listSaleOrders } from '../api/sales'
import { listWarehouses } from '../api/stock'
import { useAuth } from '../auth/AuthContext'
import StatusBadge from '../components/StatusBadge'

export default function DeliveryRoutesPage() {
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const canManage = hasRole('logistique')

  const { data: routes } = useQuery({ queryKey: ['delivery-routes'], queryFn: listDeliveryRoutes })
  const { data: drivers } = useQuery({ queryKey: ['drivers'], queryFn: listDrivers })
  const { data: vehicles } = useQuery({ queryKey: ['vehicles'], queryFn: listVehicles })
  const { data: warehouses } = useQuery({ queryKey: ['warehouses'], queryFn: listWarehouses })
  const { data: orders } = useQuery({ queryKey: ['sale-orders'], queryFn: listSaleOrders })
  const { data: deliveries } = useQuery({ queryKey: ['deliveries'], queryFn: listDeliveries })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['delivery-routes'] })
    queryClient.invalidateQueries({ queryKey: ['deliveries'] })
  }
  const createRouteMutation = useMutation({ mutationFn: createDeliveryRoute, onSuccess: invalidate })
  const loadMutation = useMutation({ mutationFn: loadRoute, onSuccess: invalidate })
  const startMutation = useMutation({ mutationFn: startRoute, onSuccess: invalidate })
  const finishMutation = useMutation({ mutationFn: finishRoute, onSuccess: invalidate })
  const closeMutation = useMutation({ mutationFn: closeRoute, onSuccess: invalidate })
  const addDeliveryMutation = useMutation({ mutationFn: createDelivery, onSuccess: invalidate })

  const [driverId, setDriverId] = useState('')
  const [vehicleId, setVehicleId] = useState('')
  const [warehouseId, setWarehouseId] = useState('')
  const [routeDate, setRouteDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [pendingOrderByRoute, setPendingOrderByRoute] = useState<Record<number, string>>({})

  const deliveredOrderIds = new Set(deliveries?.map((d) => d.sale_order_id) ?? [])
  const deliverableOrders = orders?.filter((o) => o.state === 'commande' && !deliveredOrderIds.has(o.id)) ?? []

  function submitRoute(e: FormEvent) {
    e.preventDefault()
    createRouteMutation.mutate({
      driver_id: Number(driverId),
      vehicle_id: Number(vehicleId),
      warehouse_id: warehouseId ? Number(warehouseId) : undefined,
      route_date: routeDate,
    })
    setDriverId('')
    setVehicleId('')
    setWarehouseId('')
  }

  return (
    <div>
      <h1>Tournees de livraison</h1>
      <table className="data-table">
        <thead>
          <tr>
            <th>Reference</th>
            <th>Chauffeur</th>
            <th>Vehicule</th>
            <th>Entrepot</th>
            <th>Date</th>
            <th>Statut</th>
            <th>Livraisons</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {routes?.map((r) => (
            <tr key={r.id}>
              <td>{r.reference}</td>
              <td>{drivers?.find((d) => d.id === r.driver_id)?.name ?? r.driver_id}</td>
              <td>{vehicles?.find((v) => v.id === r.vehicle_id)?.name ?? r.vehicle_id}</td>
              <td>{warehouses?.find((w) => w.id === r.warehouse_id)?.name ?? '-'}</td>
              <td>{r.route_date}</td>
              <td>
                <StatusBadge status={r.state} />
              </td>
              <td>
                {r.deliveries.map((d) => (
                  <div key={d.id} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                    {d.reference} <StatusBadge status={d.state} />
                  </div>
                ))}
                {canManage && r.state === 'planifiee' && (
                  <div>
                    <select
                      value={pendingOrderByRoute[r.id] ?? ''}
                      onChange={(e) => setPendingOrderByRoute((prev) => ({ ...prev, [r.id]: e.target.value }))}
                    >
                      <option value="">Commande a livrer</option>
                      {deliverableOrders.map((o) => (
                        <option key={o.id} value={o.id}>
                          {o.reference}
                        </option>
                      ))}
                    </select>
                    <button
                      disabled={!pendingOrderByRoute[r.id]}
                      onClick={() =>
                        addDeliveryMutation.mutate({ route_id: r.id, sale_order_id: Number(pendingOrderByRoute[r.id]) })
                      }
                    >
                      Ajouter
                    </button>
                  </div>
                )}
              </td>
              <td>
                {canManage && r.state === 'planifiee' && (
                  <button onClick={() => loadMutation.mutate(r.id)}>Charger</button>
                )}
                {canManage && r.state === 'chargee' && (
                  <button onClick={() => startMutation.mutate(r.id)}>Demarrer</button>
                )}
                {canManage && r.state === 'en_livraison' && (
                  <button onClick={() => finishMutation.mutate(r.id)}>Terminer</button>
                )}
                {canManage && r.state === 'livree' && (
                  <button onClick={() => closeMutation.mutate(r.id)}>Cloturer</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {canManage && (
        <form className="inline-form" onSubmit={submitRoute}>
          <h2>Nouvelle tournee</h2>
          <select value={driverId} onChange={(e) => setDriverId(e.target.value)} required>
            <option value="">Chauffeur</option>
            {drivers?.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
          <select value={vehicleId} onChange={(e) => setVehicleId(e.target.value)} required>
            <option value="">Vehicule</option>
            {vehicles?.map((v) => (
              <option key={v.id} value={v.id}>
                {v.name}
              </option>
            ))}
          </select>
          <select value={warehouseId} onChange={(e) => setWarehouseId(e.target.value)}>
            <option value="">Entrepot de chargement (optionnel)</option>
            {warehouses?.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
          </select>
          <input type="date" value={routeDate} onChange={(e) => setRouteDate(e.target.value)} required />
          <button type="submit" disabled={createRouteMutation.isPending}>
            Creer
          </button>
        </form>
      )}
    </div>
  )
}
