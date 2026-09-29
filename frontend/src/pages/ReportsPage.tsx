import { useQuery } from '@tanstack/react-query'
import { FileDown, FileSpreadsheet } from 'lucide-react'
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

const currencyFormatter = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 })
function fcfa(value: number): string {
  return `${currencyFormatter.format(value)} FCFA`
}

type ReportSection = { heading: string; rows: [string, string][] }

async function exportPdf(periodStart: string, periodEnd: string, sections: ReportSection[]) {
  const [{ default: jsPDF }, { default: autoTable }] = await Promise.all([import('jspdf'), import('jspdf-autotable')])
  const doc = new jsPDF()
  doc.setFontSize(16)
  doc.text('Rapports - SAYAL ERP', 14, 18)
  doc.setFontSize(10)
  doc.setTextColor(100)
  doc.text(`Periode : du ${periodStart} au ${periodEnd}`, 14, 25)
  doc.setTextColor(0)

  let y = 32
  for (const section of sections) {
    doc.setFontSize(12)
    doc.text(section.heading, 14, y)
    autoTable(doc, {
      startY: y + 4,
      body: section.rows,
      theme: 'grid',
      styles: { fontSize: 10 },
      margin: { left: 14, right: 14 },
    })
    y = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 12
  }

  doc.save(`rapport-sayal-${periodStart}_${periodEnd}.pdf`)
}

function exportCsv(periodStart: string, periodEnd: string, sections: ReportSection[]) {
  const escape = (value: string) => `"${value.replace(/"/g, '""')}"`
  const lines: string[] = [escape('Rapports - SAYAL ERP'), escape(`Periode : du ${periodStart} au ${periodEnd}`), '']
  for (const section of sections) {
    lines.push(escape(section.heading))
    for (const [label, value] of section.rows) {
      lines.push(`${escape(label)},${escape(value)}`)
    }
    lines.push('')
  }
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `rapport-sayal-${periodStart}_${periodEnd}.csv`
  link.click()
  URL.revokeObjectURL(url)
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

  const sections: ReportSection[] = []
  if (canSeeSales && salesSummary) {
    sections.push({
      heading: 'Ventes',
      rows: [
        ['Total commandes confirmees', fcfa(salesSummary.total_confirmed_sales)],
        ['Total facture (net des avoirs)', fcfa(salesSummary.total_invoiced)],
        ['Total encaisse', fcfa(salesSummary.total_collected)],
      ],
    })
  }
  if (canSeeHr && hrSummary) {
    sections.push({
      heading: 'Ressources humaines',
      rows: [
        ['Employes actifs', String(hrSummary.active_employee_count)],
        ["En conge aujourd'hui", String(hrSummary.on_leave_today_count)],
        ['Cout de la masse salariale (periode)', fcfa(hrSummary.payroll_cost)],
      ],
    })
  }

  return (
    <div>
      <h1>Rapports</h1>
      <div className="inline-form" style={{ marginBottom: 16, flexDirection: 'row', alignItems: 'flex-end', gap: 16, flexWrap: 'wrap' }}>
        <label>
          Du
          <input type="date" value={periodStart} onChange={(e) => setPeriodStart(e.target.value)} />
        </label>
        <label>
          Au
          <input type="date" value={periodEnd} onChange={(e) => setPeriodEnd(e.target.value)} />
        </label>
        {sections.length > 0 && (
          <div style={{ display: 'flex', gap: 8 }}>
            <button type="button" onClick={() => exportPdf(periodStart, periodEnd, sections)}>
              <FileDown size={15} /> Exporter PDF
            </button>
            <button type="button" onClick={() => exportCsv(periodStart, periodEnd, sections)}>
              <FileSpreadsheet size={15} /> Exporter Excel
            </button>
          </div>
        )}
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
