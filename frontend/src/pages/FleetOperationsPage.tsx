import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { listCashSessions, listBankAccounts, type PaymentMethod } from '../api/finance'
import {
  cancelVehicleMaintenance,
  completeVehicleMaintenance,
  createFuelLog,
  createVehicleDocument,
  createVehicleMaintenance,
  listExpiringVehicleDocuments,
  listFuelLogs,
  listVehicleDocuments,
  listVehicleMaintenances,
  type VehicleDocumentType,
} from '../api/fleetOps'
import { listVehicles } from '../api/deliveries'
import { useAuth } from '../auth/AuthContext'

export default function FleetOperationsPage() {
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const canManage = hasRole('logistique')

  const { data: vehicles } = useQuery({ queryKey: ['vehicles'], queryFn: listVehicles })
  const { data: fuelLogs } = useQuery({ queryKey: ['fuel-logs'], queryFn: () => listFuelLogs() })
  const { data: maintenances } = useQuery({ queryKey: ['vehicle-maintenances'], queryFn: () => listVehicleMaintenances() })
  const { data: documents } = useQuery({ queryKey: ['vehicle-documents'], queryFn: () => listVehicleDocuments() })
  const { data: expiringDocs } = useQuery({ queryKey: ['vehicle-documents-expiring'], queryFn: () => listExpiringVehicleDocuments(30) })
  const { data: cashSessions } = useQuery({ queryKey: ['cash-sessions'], queryFn: listCashSessions })
  const { data: bankAccounts } = useQuery({ queryKey: ['bank-accounts'], queryFn: listBankAccounts })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['fuel-logs'] })
    queryClient.invalidateQueries({ queryKey: ['vehicle-maintenances'] })
    queryClient.invalidateQueries({ queryKey: ['vehicle-documents'] })
    queryClient.invalidateQueries({ queryKey: ['vehicle-documents-expiring'] })
    queryClient.invalidateQueries({ queryKey: ['cash-sessions'] })
    queryClient.invalidateQueries({ queryKey: ['bank-accounts'] })
  }
  const createFuelMutation = useMutation({ mutationFn: createFuelLog, onSuccess: invalidate })
  const createMaintenanceMutation = useMutation({ mutationFn: createVehicleMaintenance, onSuccess: invalidate })
  const completeMaintenanceMutation = useMutation({ mutationFn: completeVehicleMaintenance, onSuccess: invalidate })
  const cancelMaintenanceMutation = useMutation({ mutationFn: cancelVehicleMaintenance, onSuccess: invalidate })
  const createDocumentMutation = useMutation({ mutationFn: createVehicleDocument, onSuccess: invalidate })

  const openSessions = cashSessions?.filter((s) => s.state === 'open') ?? []

  const [fuelVehicleId, setFuelVehicleId] = useState('')
  const [fuelLiters, setFuelLiters] = useState('')
  const [fuelUnitPrice, setFuelUnitPrice] = useState('')
  const [fuelMethod, setFuelMethod] = useState<PaymentMethod>('especes')
  const [fuelTarget, setFuelTarget] = useState('')

  const [maintVehicleId, setMaintVehicleId] = useState('')
  const [maintDescription, setMaintDescription] = useState('')
  const [maintCost, setMaintCost] = useState('0')
  const [maintMethod, setMaintMethod] = useState<PaymentMethod>('especes')
  const [maintTarget, setMaintTarget] = useState('')

  const [docVehicleId, setDocVehicleId] = useState('')
  const [docType, setDocType] = useState<VehicleDocumentType>('assurance')
  const [docStart, setDocStart] = useState('')
  const [docEnd, setDocEnd] = useState('')
  const [docCost, setDocCost] = useState('0')

  function submitFuel(e: FormEvent) {
    e.preventDefault()
    if (!fuelVehicleId || !fuelLiters || !fuelUnitPrice) return
    createFuelMutation.mutate({
      vehicle_id: Number(fuelVehicleId),
      log_date: new Date().toISOString().slice(0, 10),
      liters: Number(fuelLiters),
      unit_price: Number(fuelUnitPrice),
      payment_method: fuelMethod,
      cash_session_id: fuelMethod === 'especes' && fuelTarget ? Number(fuelTarget) : undefined,
      bank_account_id: fuelMethod === 'banque' && fuelTarget ? Number(fuelTarget) : undefined,
    })
    setFuelLiters('')
    setFuelUnitPrice('')
  }

  function submitMaintenance(e: FormEvent) {
    e.preventDefault()
    if (!maintVehicleId || !maintDescription) return
    createMaintenanceMutation.mutate({
      vehicle_id: Number(maintVehicleId),
      maintenance_date: new Date().toISOString().slice(0, 10),
      description: maintDescription,
      cost: Number(maintCost || 0),
      payment_method: maintMethod,
      cash_session_id: maintMethod === 'especes' && maintTarget ? Number(maintTarget) : undefined,
      bank_account_id: maintMethod === 'banque' && maintTarget ? Number(maintTarget) : undefined,
    })
    setMaintDescription('')
    setMaintCost('0')
  }

  function submitDocument(e: FormEvent) {
    e.preventDefault()
    if (!docVehicleId || !docStart || !docEnd) return
    createDocumentMutation.mutate({
      vehicle_id: Number(docVehicleId),
      document_type: docType,
      start_date: docStart,
      end_date: docEnd,
      cost: Number(docCost || 0),
    })
    setDocStart('')
    setDocEnd('')
    setDocCost('0')
  }

  function vehicleName(id: number) {
    return vehicles?.find((v) => v.id === id)?.name ?? id
  }

  return (
    <div>
      <h1>Carburant &amp; entretien</h1>

      {expiringDocs && expiringDocs.length > 0 && (
        <div className="error" style={{ marginBottom: 16 }}>
          {expiringDocs.length} document(s) vehicule expirent dans les 30 prochains jours :{' '}
          {expiringDocs.map((d) => `${vehicleName(d.vehicle_id)} (${d.document_type}, ${d.end_date})`).join(', ')}
        </div>
      )}

      <h2>Plein de carburant</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>Vehicule</th>
            <th>Date</th>
            <th>Litres</th>
            <th>Prix unitaire</th>
            <th>Cout total</th>
            <th>Mode</th>
          </tr>
        </thead>
        <tbody>
          {fuelLogs?.map((f) => (
            <tr key={f.id}>
              <td>{vehicleName(f.vehicle_id)}</td>
              <td>{f.log_date}</td>
              <td>{f.liters}</td>
              <td>{f.unit_price}</td>
              <td>{f.total_cost}</td>
              <td>{f.payment_method}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {canManage && (
        <form className="inline-form" onSubmit={submitFuel}>
          <select value={fuelVehicleId} onChange={(e) => setFuelVehicleId(e.target.value)} required>
            <option value="">Vehicule</option>
            {vehicles?.map((v) => (
              <option key={v.id} value={v.id}>
                {v.name}
              </option>
            ))}
          </select>
          <input type="number" placeholder="Litres" value={fuelLiters} onChange={(e) => setFuelLiters(e.target.value)} required />
          <input
            type="number"
            placeholder="Prix unitaire"
            value={fuelUnitPrice}
            onChange={(e) => setFuelUnitPrice(e.target.value)}
            required
          />
          <select value={fuelMethod} onChange={(e) => setFuelMethod(e.target.value as PaymentMethod)}>
            <option value="especes">Especes</option>
            <option value="banque">Banque</option>
          </select>
          <select value={fuelTarget} onChange={(e) => setFuelTarget(e.target.value)} required>
            <option value="">{fuelMethod === 'especes' ? 'Session de caisse' : 'Compte bancaire'}</option>
            {(fuelMethod === 'especes' ? openSessions : bankAccounts)?.map((t) => (
              <option key={t.id} value={t.id}>
                {'register_id' in t ? `Caisse #${t.register_id} (session ${t.id})` : t.name}
              </option>
            ))}
          </select>
          <button type="submit" disabled={createFuelMutation.isPending}>
            Enregistrer
          </button>
        </form>
      )}

      <h2>Entretiens</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>Vehicule</th>
            <th>Date</th>
            <th>Description</th>
            <th>Cout</th>
            <th>Statut</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {maintenances?.map((m) => (
            <tr key={m.id}>
              <td>{vehicleName(m.vehicle_id)}</td>
              <td>{m.maintenance_date}</td>
              <td>{m.description}</td>
              <td>{m.cost}</td>
              <td>{m.state}</td>
              <td>
                {canManage && m.state === 'planifiee' && (
                  <>
                    <button onClick={() => completeMaintenanceMutation.mutate(m.id)}>Terminer</button>
                    <button onClick={() => cancelMaintenanceMutation.mutate(m.id)}>Annuler</button>
                  </>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {canManage && (
        <form className="inline-form" onSubmit={submitMaintenance}>
          <select value={maintVehicleId} onChange={(e) => setMaintVehicleId(e.target.value)} required>
            <option value="">Vehicule</option>
            {vehicles?.map((v) => (
              <option key={v.id} value={v.id}>
                {v.name}
              </option>
            ))}
          </select>
          <input
            placeholder="Description"
            value={maintDescription}
            onChange={(e) => setMaintDescription(e.target.value)}
            required
          />
          <input type="number" placeholder="Cout" value={maintCost} onChange={(e) => setMaintCost(e.target.value)} />
          <select value={maintMethod} onChange={(e) => setMaintMethod(e.target.value as PaymentMethod)}>
            <option value="especes">Especes</option>
            <option value="banque">Banque</option>
          </select>
          {Number(maintCost || 0) > 0 && (
            <select value={maintTarget} onChange={(e) => setMaintTarget(e.target.value)} required>
              <option value="">{maintMethod === 'especes' ? 'Session de caisse' : 'Compte bancaire'}</option>
              {(maintMethod === 'especes' ? openSessions : bankAccounts)?.map((t) => (
                <option key={t.id} value={t.id}>
                  {'register_id' in t ? `Caisse #${t.register_id} (session ${t.id})` : t.name}
                </option>
              ))}
            </select>
          )}
          <button type="submit" disabled={createMaintenanceMutation.isPending}>
            Planifier
          </button>
        </form>
      )}

      <h2>Documents vehicule (assurance, controle technique, vignette)</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>Vehicule</th>
            <th>Type</th>
            <th>Reference</th>
            <th>Debut</th>
            <th>Fin</th>
            <th>Cout</th>
          </tr>
        </thead>
        <tbody>
          {documents?.map((d) => (
            <tr key={d.id}>
              <td>{vehicleName(d.vehicle_id)}</td>
              <td>{d.document_type}</td>
              <td>{d.reference ?? '-'}</td>
              <td>{d.start_date}</td>
              <td>{d.end_date}</td>
              <td>{d.cost}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {canManage && (
        <form className="inline-form" onSubmit={submitDocument}>
          <select value={docVehicleId} onChange={(e) => setDocVehicleId(e.target.value)} required>
            <option value="">Vehicule</option>
            {vehicles?.map((v) => (
              <option key={v.id} value={v.id}>
                {v.name}
              </option>
            ))}
          </select>
          <select value={docType} onChange={(e) => setDocType(e.target.value as VehicleDocumentType)}>
            <option value="assurance">Assurance</option>
            <option value="controle_technique">Controle technique</option>
            <option value="vignette">Vignette</option>
            <option value="autre">Autre</option>
          </select>
          <input type="date" placeholder="Debut" value={docStart} onChange={(e) => setDocStart(e.target.value)} required />
          <input type="date" placeholder="Fin" value={docEnd} onChange={(e) => setDocEnd(e.target.value)} required />
          <input type="number" placeholder="Cout" value={docCost} onChange={(e) => setDocCost(e.target.value)} />
          <button type="submit" disabled={createDocumentMutation.isPending}>
            Enregistrer
          </button>
        </form>
      )}
    </div>
  )
}
