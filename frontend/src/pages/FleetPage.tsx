import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { createDriver, createVehicle, listDrivers, listVehicles } from '../api/deliveries'
import { listUsers } from '../api/users'
import { useAuth } from '../auth/AuthContext'

export default function FleetPage() {
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const canManage = hasRole('logistique')
  const canSeeUsers = hasRole('direction_generale')

  const { data: vehicles } = useQuery({ queryKey: ['vehicles'], queryFn: listVehicles })
  const { data: drivers } = useQuery({ queryKey: ['drivers'], queryFn: listDrivers })
  const { data: users } = useQuery({ queryKey: ['users'], queryFn: listUsers, enabled: canSeeUsers })

  const vehicleMutation = useMutation({
    mutationFn: createVehicle,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['vehicles'] }),
  })
  const driverMutation = useMutation({
    mutationFn: createDriver,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['drivers'] }),
  })

  const [vehicleName, setVehicleName] = useState('')
  const [plateNumber, setPlateNumber] = useState('')
  const [driverName, setDriverName] = useState('')
  const [driverUserId, setDriverUserId] = useState('')

  function submitVehicle(e: FormEvent) {
    e.preventDefault()
    vehicleMutation.mutate({ name: vehicleName, plate_number: plateNumber })
    setVehicleName('')
    setPlateNumber('')
  }

  function submitDriver(e: FormEvent) {
    e.preventDefault()
    driverMutation.mutate({ name: driverName, user_id: driverUserId ? Number(driverUserId) : undefined })
    setDriverName('')
    setDriverUserId('')
  }

  return (
    <div>
      <h1>Vehicules &amp; chauffeurs</h1>

      <h2>Vehicules</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>Nom</th>
            <th>Immatriculation</th>
          </tr>
        </thead>
        <tbody>
          {vehicles?.map((v) => (
            <tr key={v.id}>
              <td>{v.name}</td>
              <td>{v.plate_number}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {canManage && (
        <form className="inline-form" onSubmit={submitVehicle}>
          <input placeholder="Nom du vehicule" value={vehicleName} onChange={(e) => setVehicleName(e.target.value)} required />
          <input placeholder="Immatriculation" value={plateNumber} onChange={(e) => setPlateNumber(e.target.value)} required />
          <button type="submit" disabled={vehicleMutation.isPending}>
            Ajouter
          </button>
        </form>
      )}

      <h2>Chauffeurs</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>Nom</th>
            <th>Compte utilisateur lie</th>
          </tr>
        </thead>
        <tbody>
          {drivers?.map((d) => (
            <tr key={d.id}>
              <td>{d.name}</td>
              <td>{users?.find((u) => u.id === d.user_id)?.name ?? (d.user_id ?? '-')}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {canManage && (
        <form className="inline-form" onSubmit={submitDriver}>
          <input placeholder="Nom du chauffeur" value={driverName} onChange={(e) => setDriverName(e.target.value)} required />
          {canSeeUsers && (
            <select value={driverUserId} onChange={(e) => setDriverUserId(e.target.value)}>
              <option value="">Compte utilisateur (optionnel, pour "Mes livraisons")</option>
              {users?.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.name}
                </option>
              ))}
            </select>
          )}
          <button type="submit" disabled={driverMutation.isPending}>
            Ajouter
          </button>
        </form>
      )}
    </div>
  )
}
