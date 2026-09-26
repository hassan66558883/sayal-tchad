import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import {
  createSalesRep,
  createSalesTarget,
  getSalesRepCommission,
  listSalesReps,
  listSalesTargets,
} from '../api/commercial'
import { listUsers } from '../api/users'
import { useAuth } from '../auth/AuthContext'

function firstOfMonth(): string {
  const now = new Date()
  return new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10)
}

function lastOfMonth(): string {
  const now = new Date()
  return new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().slice(0, 10)
}

export default function CommercialPage() {
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const canManage = hasRole('direction_generale')

  const { data: reps } = useQuery({ queryKey: ['sales-reps'], queryFn: listSalesReps })
  const { data: targets } = useQuery({ queryKey: ['sales-targets'], queryFn: listSalesTargets })
  const { data: users } = useQuery({ queryKey: ['users'], queryFn: listUsers, enabled: canManage })

  const periodStart = firstOfMonth()
  const periodEnd = lastOfMonth()
  const commissionQueries = useQueries({
    queries: (reps ?? []).map((r) => ({
      queryKey: ['sales-rep-commission', r.id, periodStart, periodEnd],
      queryFn: () => getSalesRepCommission(r.id, periodStart, periodEnd),
    })),
  })
  const commissionByRep = new Map((reps ?? []).map((r, i) => [r.id, commissionQueries[i]?.data?.commission]))

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['sales-reps'] })
    queryClient.invalidateQueries({ queryKey: ['sales-targets'] })
  }
  const createRepMutation = useMutation({ mutationFn: createSalesRep, onSuccess: invalidate })
  const createTargetMutation = useMutation({ mutationFn: createSalesTarget, onSuccess: invalidate })

  const [repName, setRepName] = useState('')
  const [repUserId, setRepUserId] = useState('')
  const [repCommissionRate, setRepCommissionRate] = useState('0')

  const [targetRepId, setTargetRepId] = useState('')
  const [targetStart, setTargetStart] = useState(periodStart)
  const [targetEnd, setTargetEnd] = useState(periodEnd)
  const [targetAmount, setTargetAmount] = useState('')

  function submitRep(e: FormEvent) {
    e.preventDefault()
    createRepMutation.mutate({
      name: repName,
      user_id: repUserId ? Number(repUserId) : undefined,
      commission_rate: Number(repCommissionRate || 0),
    })
    setRepName('')
    setRepUserId('')
    setRepCommissionRate('0')
  }

  function submitTarget(e: FormEvent) {
    e.preventDefault()
    if (!targetRepId || !targetAmount) return
    createTargetMutation.mutate({
      sales_rep_id: Number(targetRepId),
      period_start: targetStart,
      period_end: targetEnd,
      target_amount: Number(targetAmount),
    })
    setTargetAmount('')
  }

  return (
    <div>
      <h1>Commercial</h1>

      <h2>Commerciaux</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>Nom</th>
            <th>Taux de commission</th>
            <th>Commission ce mois-ci</th>
          </tr>
        </thead>
        <tbody>
          {reps?.map((r) => (
            <tr key={r.id}>
              <td>{r.name}</td>
              <td>{r.commission_rate}%</td>
              <td>{commissionByRep.get(r.id) ?? '...'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {canManage && (
        <form className="inline-form" onSubmit={submitRep}>
          <h2>Nouveau commercial</h2>
          <input placeholder="Nom" value={repName} onChange={(e) => setRepName(e.target.value)} required />
          <select value={repUserId} onChange={(e) => setRepUserId(e.target.value)}>
            <option value="">Compte utilisateur (optionnel)</option>
            {users?.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name}
              </option>
            ))}
          </select>
          <input
            type="number"
            placeholder="Taux de commission %"
            value={repCommissionRate}
            onChange={(e) => setRepCommissionRate(e.target.value)}
          />
          <button type="submit" disabled={createRepMutation.isPending}>
            Ajouter
          </button>
        </form>
      )}

      <h2>Objectifs commerciaux</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>Commercial</th>
            <th>Periode</th>
            <th>Objectif</th>
            <th>Realise</th>
            <th>Atteinte</th>
          </tr>
        </thead>
        <tbody>
          {targets?.map((t) => (
            <tr key={t.id}>
              <td>{reps?.find((r) => r.id === t.sales_rep_id)?.name ?? t.sales_rep_id}</td>
              <td>
                {t.period_start} - {t.period_end}
              </td>
              <td>{t.target_amount}</td>
              <td>{t.achieved_amount}</td>
              <td>{t.achievement_percent !== null ? `${t.achievement_percent.toFixed(1)}%` : '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {canManage && (
        <form className="inline-form" onSubmit={submitTarget}>
          <h2>Nouvel objectif</h2>
          <select value={targetRepId} onChange={(e) => setTargetRepId(e.target.value)} required>
            <option value="">Commercial</option>
            {reps?.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
          <input type="date" value={targetStart} onChange={(e) => setTargetStart(e.target.value)} required />
          <input type="date" value={targetEnd} onChange={(e) => setTargetEnd(e.target.value)} required />
          <input
            type="number"
            placeholder="Montant objectif"
            value={targetAmount}
            onChange={(e) => setTargetAmount(e.target.value)}
            required
          />
          <button type="submit" disabled={createTargetMutation.isPending}>
            Creer
          </button>
        </form>
      )}
    </div>
  )
}
