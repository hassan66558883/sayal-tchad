import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { listBankAccounts, listCashSessions, type PaymentMethod } from '../api/finance'
import {
  approveLeaveRequest,
  createEmployee,
  createLeaveRequest,
  createPayslip,
  listEmployees,
  listLeaveRequests,
  listPayslips,
  rejectLeaveRequest,
  validatePayslip,
  type LeaveType,
} from '../api/hr'
import { listUsers } from '../api/users'
import { useAuth } from '../auth/AuthContext'

export default function HRPage() {
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const canManage = hasRole('rh')

  const { data: employees } = useQuery({ queryKey: ['employees'], queryFn: listEmployees })
  const { data: leaveRequests } = useQuery({ queryKey: ['leave-requests'], queryFn: listLeaveRequests })
  const { data: payslips } = useQuery({ queryKey: ['payslips'], queryFn: listPayslips, enabled: canManage })
  const { data: users } = useQuery({ queryKey: ['users'], queryFn: listUsers, enabled: canManage })
  const { data: cashSessions } = useQuery({ queryKey: ['cash-sessions'], queryFn: listCashSessions, enabled: canManage })
  const { data: bankAccounts } = useQuery({ queryKey: ['bank-accounts'], queryFn: listBankAccounts, enabled: canManage })
  const openSessions = cashSessions?.filter((s) => s.state === 'open') ?? []

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['employees'] })
    queryClient.invalidateQueries({ queryKey: ['leave-requests'] })
    queryClient.invalidateQueries({ queryKey: ['payslips'] })
    queryClient.invalidateQueries({ queryKey: ['cash-sessions'] })
    queryClient.invalidateQueries({ queryKey: ['bank-accounts'] })
  }
  const createEmployeeMutation = useMutation({ mutationFn: createEmployee, onSuccess: invalidate })
  const createLeaveMutation = useMutation({ mutationFn: createLeaveRequest, onSuccess: invalidate })
  const approveMutation = useMutation({ mutationFn: approveLeaveRequest, onSuccess: invalidate })
  const rejectMutation = useMutation({ mutationFn: rejectLeaveRequest, onSuccess: invalidate })
  const createPayslipMutation = useMutation({ mutationFn: createPayslip, onSuccess: invalidate })
  const validatePayslipMutation = useMutation({ mutationFn: validatePayslip, onSuccess: invalidate })

  const [empName, setEmpName] = useState('')
  const [empUserId, setEmpUserId] = useState('')
  const [empPosition, setEmpPosition] = useState('')
  const [empHireDate, setEmpHireDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [empSalary, setEmpSalary] = useState('')

  const [leaveEmployeeId, setLeaveEmployeeId] = useState('')
  const [leaveType, setLeaveType] = useState<LeaveType>('conge_paye')
  const [leaveStart, setLeaveStart] = useState('')
  const [leaveEnd, setLeaveEnd] = useState('')

  const [payEmployeeId, setPayEmployeeId] = useState('')
  const [payStart, setPayStart] = useState('')
  const [payEnd, setPayEnd] = useState('')
  const [payBase, setPayBase] = useState('')
  const [payBonuses, setPayBonuses] = useState('0')
  const [payDeductions, setPayDeductions] = useState('0')
  const [payMethod, setPayMethod] = useState<PaymentMethod>('especes')
  const [payTarget, setPayTarget] = useState('')

  function submitEmployee(e: FormEvent) {
    e.preventDefault()
    createEmployeeMutation.mutate({
      name: empName,
      user_id: empUserId ? Number(empUserId) : undefined,
      position: empPosition,
      hire_date: empHireDate,
      base_salary: Number(empSalary || 0),
    })
    setEmpName('')
    setEmpUserId('')
    setEmpPosition('')
    setEmpSalary('')
  }

  function submitLeave(e: FormEvent) {
    e.preventDefault()
    if (!leaveEmployeeId || !leaveStart || !leaveEnd) return
    createLeaveMutation.mutate({
      employee_id: Number(leaveEmployeeId),
      leave_type: leaveType,
      start_date: leaveStart,
      end_date: leaveEnd,
    })
    setLeaveStart('')
    setLeaveEnd('')
  }

  function submitPayslip(e: FormEvent) {
    e.preventDefault()
    if (!payEmployeeId || !payStart || !payEnd || !payBase) return
    createPayslipMutation.mutate({
      employee_id: Number(payEmployeeId),
      period_start: payStart,
      period_end: payEnd,
      base_salary: Number(payBase),
      bonuses: Number(payBonuses || 0),
      deductions: Number(payDeductions || 0),
      payment_method: payMethod,
      cash_session_id: payMethod === 'especes' && payTarget ? Number(payTarget) : undefined,
      bank_account_id: payMethod === 'banque' && payTarget ? Number(payTarget) : undefined,
    })
    setPayBase('')
    setPayBonuses('0')
    setPayDeductions('0')
  }

  function employeeName(id: number) {
    return employees?.find((e) => e.id === id)?.name ?? id
  }

  return (
    <div>
      <h1>Ressources humaines</h1>

      <h2>Employes</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>Nom</th>
            <th>Poste</th>
            <th>Date d'embauche</th>
            <th>Salaire de base</th>
          </tr>
        </thead>
        <tbody>
          {employees?.map((emp) => (
            <tr key={emp.id}>
              <td>{emp.name}</td>
              <td>{emp.position}</td>
              <td>{emp.hire_date}</td>
              <td>{emp.base_salary}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {canManage && (
        <form className="inline-form" onSubmit={submitEmployee}>
          <h3>Nouvel employe</h3>
          <input placeholder="Nom" value={empName} onChange={(e) => setEmpName(e.target.value)} required />
          <select value={empUserId} onChange={(e) => setEmpUserId(e.target.value)}>
            <option value="">Compte utilisateur (optionnel)</option>
            {users?.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name}
              </option>
            ))}
          </select>
          <input placeholder="Poste" value={empPosition} onChange={(e) => setEmpPosition(e.target.value)} required />
          <input type="date" value={empHireDate} onChange={(e) => setEmpHireDate(e.target.value)} required />
          <input
            type="number"
            placeholder="Salaire de base"
            value={empSalary}
            onChange={(e) => setEmpSalary(e.target.value)}
          />
          <button type="submit" disabled={createEmployeeMutation.isPending}>
            Ajouter
          </button>
        </form>
      )}

      <h2>Demandes de conge</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>Employe</th>
            <th>Type</th>
            <th>Debut</th>
            <th>Fin</th>
            <th>Statut</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {leaveRequests?.map((r) => (
            <tr key={r.id}>
              <td>{employeeName(r.employee_id)}</td>
              <td>{r.leave_type}</td>
              <td>{r.start_date}</td>
              <td>{r.end_date}</td>
              <td>{r.state}</td>
              <td>
                {canManage && r.state === 'en_attente' && (
                  <>
                    <button onClick={() => approveMutation.mutate(r.id)}>Approuver</button>
                    <button onClick={() => rejectMutation.mutate(r.id)}>Refuser</button>
                  </>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <form className="inline-form" onSubmit={submitLeave}>
        <h3>Nouvelle demande de conge</h3>
        <select value={leaveEmployeeId} onChange={(e) => setLeaveEmployeeId(e.target.value)} required>
          <option value="">Employe</option>
          {employees?.map((emp) => (
            <option key={emp.id} value={emp.id}>
              {emp.name}
            </option>
          ))}
        </select>
        <select value={leaveType} onChange={(e) => setLeaveType(e.target.value as LeaveType)}>
          <option value="conge_paye">Conge paye</option>
          <option value="maladie">Maladie</option>
          <option value="autre">Autre</option>
        </select>
        <input type="date" value={leaveStart} onChange={(e) => setLeaveStart(e.target.value)} required />
        <input type="date" value={leaveEnd} onChange={(e) => setLeaveEnd(e.target.value)} required />
        <button type="submit" disabled={createLeaveMutation.isPending}>
          Soumettre
        </button>
      </form>

      {canManage && (
        <>
          <h2>Bulletins de paie</h2>
          <table className="data-table">
            <thead>
              <tr>
                <th>Reference</th>
                <th>Employe</th>
                <th>Periode</th>
                <th>Net a payer</th>
                <th>Statut</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {payslips?.map((p) => (
                <tr key={p.id}>
                  <td>{p.reference}</td>
                  <td>{employeeName(p.employee_id)}</td>
                  <td>
                    {p.period_start} - {p.period_end}
                  </td>
                  <td>{p.net_pay}</td>
                  <td>{p.state}</td>
                  <td>
                    {p.state === 'draft' && (
                      <button onClick={() => validatePayslipMutation.mutate(p.id)}>Valider</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <form className="inline-form" onSubmit={submitPayslip}>
            <h3>Nouveau bulletin</h3>
            <select value={payEmployeeId} onChange={(e) => setPayEmployeeId(e.target.value)} required>
              <option value="">Employe</option>
              {employees?.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.name}
                </option>
              ))}
            </select>
            <input type="date" value={payStart} onChange={(e) => setPayStart(e.target.value)} required />
            <input type="date" value={payEnd} onChange={(e) => setPayEnd(e.target.value)} required />
            <input
              type="number"
              placeholder="Salaire de base"
              value={payBase}
              onChange={(e) => setPayBase(e.target.value)}
              required
            />
            <input
              type="number"
              placeholder="Primes"
              value={payBonuses}
              onChange={(e) => setPayBonuses(e.target.value)}
            />
            <input
              type="number"
              placeholder="Retenues"
              value={payDeductions}
              onChange={(e) => setPayDeductions(e.target.value)}
            />
            <select value={payMethod} onChange={(e) => setPayMethod(e.target.value as PaymentMethod)}>
              <option value="especes">Especes</option>
              <option value="banque">Banque</option>
            </select>
            <select value={payTarget} onChange={(e) => setPayTarget(e.target.value)} required>
              <option value="">{payMethod === 'especes' ? 'Session de caisse' : 'Compte bancaire'}</option>
              {(payMethod === 'especes' ? openSessions : bankAccounts)?.map((t) => (
                <option key={t.id} value={t.id}>
                  {'register_id' in t ? `Caisse #${t.register_id} (session ${t.id})` : t.name}
                </option>
              ))}
            </select>
            <button type="submit" disabled={createPayslipMutation.isPending}>
              Creer
            </button>
          </form>
        </>
      )}
    </div>
  )
}
