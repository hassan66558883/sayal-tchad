import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { getHrSummary, getSalesSummary } from '../api/reports'
import { useAuth } from '../auth/AuthContext'

function firstOfMonth(): string {
  const now = new Date()
  return new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10)
}

function lastOfMonth(): string {
  const now = new Date()
  return new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().slice(0, 10)
}

export default function ReportsPage() {
  const { hasRole } = useAuth()
  const [periodStart, setPeriodStart] = useState(firstOfMonth())
  const [periodEnd, setPeriodEnd] = useState(lastOfMonth())

  const canSeeSales = hasRole('direction_generale', 'comptable', 'ventes')
  const canSeeHr = hasRole('direction_generale', 'rh')

  const { data: salesSummary } = useQuery({
    queryKey: ['reports-sales-summary', periodStart, periodEnd],
    queryFn: () => getSalesSummary(periodStart, periodEnd),
    enabled: canSeeSales,
  })
  const { data: hrSummary } = useQuery({
    queryKey: ['reports-hr-summary', periodStart, periodEnd],
    queryFn: () => getHrSummary(periodStart, periodEnd),
    enabled: canSeeHr,
  })

  return (
    <div>
      <h1>Rapports</h1>
      <div className="inline-form" style={{ marginBottom: 16 }}>
        <label>
          Du
          <input type="date" value={periodStart} onChange={(e) => setPeriodStart(e.target.value)} />
        </label>
        <label>
          Au
          <input type="date" value={periodEnd} onChange={(e) => setPeriodEnd(e.target.value)} />
        </label>
      </div>

      {canSeeSales && (
        <>
          <h2>Ventes</h2>
          <table className="data-table">
            <tbody>
              <tr>
                <td>Total commandes confirmees</td>
                <td>{salesSummary?.total_confirmed_sales ?? '...'}</td>
              </tr>
              <tr>
                <td>Total facture (net des avoirs)</td>
                <td>{salesSummary?.total_invoiced ?? '...'}</td>
              </tr>
              <tr>
                <td>Total encaisse</td>
                <td>{salesSummary?.total_collected ?? '...'}</td>
              </tr>
            </tbody>
          </table>
        </>
      )}

      {canSeeHr && (
        <>
          <h2>Ressources humaines</h2>
          <table className="data-table">
            <tbody>
              <tr>
                <td>Employes actifs</td>
                <td>{hrSummary?.active_employee_count ?? '...'}</td>
              </tr>
              <tr>
                <td>En conge aujourd'hui</td>
                <td>{hrSummary?.on_leave_today_count ?? '...'}</td>
              </tr>
              <tr>
                <td>Cout de la masse salariale (periode)</td>
                <td>{hrSummary?.payroll_cost ?? '...'}</td>
              </tr>
            </tbody>
          </table>
        </>
      )}
    </div>
  )
}
