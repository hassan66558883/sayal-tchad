import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, Clock, FileWarning, Wallet } from 'lucide-react'
import { getReceivablesAging } from '../api/dashboard'

const currencyFormatter = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 })
function fcfa(value: number): string {
  return `${currencyFormatter.format(value)} FCFA`
}

function ageBadge(days: number) {
  if (days > 60) return <span className="badge badge-danger">{days} j</span>
  if (days > 30) return <span className="badge badge-warning">{days} j</span>
  return <span className="badge badge-muted">{days} j</span>
}

export default function ReceivablesPage() {
  const { data: rows } = useQuery({ queryKey: ['receivables-aging'], queryFn: getReceivablesAging })

  const totalDue = rows?.reduce((sum, r) => sum + r.amount_due, 0) ?? 0
  const overdue60 = rows?.filter((r) => r.age_days > 60).reduce((sum, r) => sum + r.amount_due, 0) ?? 0
  const oldestAge = rows && rows.length > 0 ? Math.max(...rows.map((r) => r.age_days)) : 0

  return (
    <div>
      <h1>Suivi des creances</h1>
      <p className="page-subtitle">
        Factures clients validees restant a encaisser, classees par anciennete depuis la date de facturation.
      </p>

      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-top">
            <span className="kpi-icon warning">
              <Wallet size={18} />
            </span>
          </div>
          <div className="kpi-value">{fcfa(totalDue)}</div>
          <div className="kpi-label">Total creances ouvertes</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-top">
            <span className="kpi-icon">
              <AlertTriangle size={18} />
            </span>
          </div>
          <div className="kpi-value">{fcfa(overdue60)}</div>
          <div className="kpi-label">Anciennete &gt; 60 jours</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-top">
            <span className="kpi-icon gold">
              <FileWarning size={18} />
            </span>
          </div>
          <div className="kpi-value">{rows?.length ?? 0}</div>
          <div className="kpi-label">Factures ouvertes</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-top">
            <span className="kpi-icon">
              <Clock size={18} />
            </span>
          </div>
          <div className="kpi-value">{oldestAge} j</div>
          <div className="kpi-label">Facture la plus ancienne</div>
        </div>
      </div>

      <table className="data-table">
        <thead>
          <tr>
            <th>Facture</th>
            <th>Client</th>
            <th>Date facture</th>
            <th>Montant facture</th>
            <th>Montant paye</th>
            <th>Solde</th>
            <th>Anciennete</th>
          </tr>
        </thead>
        <tbody>
          {rows?.map((r) => (
            <tr key={r.invoice_id}>
              <td>{r.reference}</td>
              <td>{r.customer_name ?? r.customer_id}</td>
              <td>{r.invoice_date}</td>
              <td>{fcfa(r.amount_total)}</td>
              <td>{fcfa(r.amount_paid)}</td>
              <td>{fcfa(r.amount_due)}</td>
              <td>{ageBadge(r.age_days)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows?.length === 0 && <p style={{ color: 'var(--text-muted)' }}>Aucune creance ouverte.</p>}
    </div>
  )
}
