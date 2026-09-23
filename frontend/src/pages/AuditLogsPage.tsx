import { useQuery } from '@tanstack/react-query'
import { listAuditLogs } from '../api/audit'

export default function AuditLogsPage() {
  const { data: entries, isLoading } = useQuery({ queryKey: ['audit-logs'], queryFn: listAuditLogs })

  return (
    <div>
      <h1>Journal d'audit</h1>
      {isLoading && <p>Chargement...</p>}
      <table className="data-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Action</th>
            <th>Modele</th>
            <th>Enregistrement</th>
            <th>Utilisateur</th>
          </tr>
        </thead>
        <tbody>
          {entries?.map((entry) => (
            <tr key={entry.id}>
              <td>{new Date(entry.created_at).toLocaleString('fr-FR')}</td>
              <td>{entry.action}</td>
              <td>{entry.model_name}</td>
              <td>{entry.record_name ?? entry.record_id}</td>
              <td>{entry.user_id ?? '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
