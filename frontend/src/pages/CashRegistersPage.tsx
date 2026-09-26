import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import {
  cancelExpense,
  closeCashSession,
  createCashRegister,
  createExpense,
  listCashRegisters,
  listCashSessions,
  listExpenses,
  openCashSession,
  validateExpense,
  type PaymentMethod,
} from '../api/finance'
import { useAuth } from '../auth/AuthContext'

export default function CashRegistersPage() {
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const canManage = hasRole('comptable')
  const canOperate = hasRole('caissier', 'comptable')

  const { data: registers } = useQuery({ queryKey: ['cash-registers'], queryFn: listCashRegisters })
  const { data: sessions } = useQuery({ queryKey: ['cash-sessions'], queryFn: listCashSessions })
  const { data: expenses } = useQuery({ queryKey: ['expenses'], queryFn: listExpenses })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['cash-registers'] })
    queryClient.invalidateQueries({ queryKey: ['cash-sessions'] })
    queryClient.invalidateQueries({ queryKey: ['expenses'] })
  }
  const createRegisterMutation = useMutation({ mutationFn: createCashRegister, onSuccess: invalidate })
  const openSessionMutation = useMutation({ mutationFn: openCashSession, onSuccess: invalidate })
  const closeSessionMutation = useMutation({
    mutationFn: ({ id, closingBalance }: { id: number; closingBalance: number }) => closeCashSession(id, closingBalance),
    onSuccess: invalidate,
  })
  const createExpenseMutation = useMutation({ mutationFn: createExpense, onSuccess: invalidate })
  const validateExpenseMutation = useMutation({ mutationFn: validateExpense, onSuccess: invalidate })
  const cancelExpenseMutation = useMutation({ mutationFn: cancelExpense, onSuccess: invalidate })

  const [registerName, setRegisterName] = useState('')
  const [registerCode, setRegisterCode] = useState('')
  const [openRegisterId, setOpenRegisterId] = useState('')
  const [openingBalance, setOpeningBalance] = useState('0')
  const [closingBalanceBySession, setClosingBalanceBySession] = useState<Record<number, string>>({})

  const [expenseCategory, setExpenseCategory] = useState('')
  const [expenseAmount, setExpenseAmount] = useState('')
  const [expenseMethod, setExpenseMethod] = useState<PaymentMethod>('especes')
  const [expenseSessionId, setExpenseSessionId] = useState('')

  const openSessions = sessions?.filter((s) => s.state === 'open') ?? []

  function submitRegister(e: FormEvent) {
    e.preventDefault()
    createRegisterMutation.mutate({ name: registerName, code: registerCode })
    setRegisterName('')
    setRegisterCode('')
  }

  function submitOpenSession(e: FormEvent) {
    e.preventDefault()
    if (!openRegisterId) return
    openSessionMutation.mutate({ register_id: Number(openRegisterId), opening_balance: Number(openingBalance || 0) })
    setOpenRegisterId('')
    setOpeningBalance('0')
  }

  function submitExpense(e: FormEvent) {
    e.preventDefault()
    createExpenseMutation.mutate({
      category: expenseCategory,
      amount: Number(expenseAmount),
      expense_date: new Date().toISOString().slice(0, 10),
      payment_method: expenseMethod,
      cash_session_id: expenseMethod === 'especes' && expenseSessionId ? Number(expenseSessionId) : undefined,
    })
    setExpenseCategory('')
    setExpenseAmount('')
  }

  return (
    <div>
      <h1>Caisse</h1>

      <h2>Caisses</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>Nom</th>
            <th>Code</th>
          </tr>
        </thead>
        <tbody>
          {registers?.map((r) => (
            <tr key={r.id}>
              <td>{r.name}</td>
              <td>{r.code}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Sessions de caisse</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>Caisse</th>
            <th>Statut</th>
            <th>Ouverture</th>
            <th>Solde reel (calcule)</th>
            <th>Cloture</th>
            <th>Ecart</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {sessions?.map((s) => (
            <tr key={s.id}>
              <td>{registers?.find((r) => r.id === s.register_id)?.name ?? s.register_id}</td>
              <td>{s.state}</td>
              <td>{s.opening_balance}</td>
              <td>{s.computed_balance}</td>
              <td>{s.closing_balance ?? '-'}</td>
              <td>{s.variance ?? '-'}</td>
              <td>
                {canOperate && s.state === 'open' && (
                  <>
                    <input
                      type="number"
                      placeholder="Montant compte"
                      style={{ width: 100 }}
                      value={closingBalanceBySession[s.id] ?? ''}
                      onChange={(e) => setClosingBalanceBySession((prev) => ({ ...prev, [s.id]: e.target.value }))}
                    />
                    <button
                      onClick={() =>
                        closeSessionMutation.mutate({ id: s.id, closingBalance: Number(closingBalanceBySession[s.id] ?? 0) })
                      }
                    >
                      Cloturer
                    </button>
                  </>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {canOperate && (
        <form className="inline-form" onSubmit={submitOpenSession}>
          <h2>Ouvrir une session</h2>
          <select value={openRegisterId} onChange={(e) => setOpenRegisterId(e.target.value)} required>
            <option value="">Caisse</option>
            {registers?.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
          <input
            type="number"
            placeholder="Fonds de caisse initial"
            value={openingBalance}
            onChange={(e) => setOpeningBalance(e.target.value)}
          />
          <button type="submit" disabled={openSessionMutation.isPending}>
            Ouvrir
          </button>
        </form>
      )}

      {canManage && (
        <form className="inline-form" onSubmit={submitRegister}>
          <h2>Nouvelle caisse</h2>
          <input placeholder="Nom" value={registerName} onChange={(e) => setRegisterName(e.target.value)} required />
          <input placeholder="Code" value={registerCode} onChange={(e) => setRegisterCode(e.target.value)} required />
          <button type="submit" disabled={createRegisterMutation.isPending}>
            Creer
          </button>
        </form>
      )}

      <h2>Depenses</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>Reference</th>
            <th>Categorie</th>
            <th>Montant</th>
            <th>Mode</th>
            <th>Statut</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {expenses?.map((exp) => (
            <tr key={exp.id}>
              <td>{exp.reference}</td>
              <td>{exp.category}</td>
              <td>{exp.amount}</td>
              <td>{exp.payment_method}</td>
              <td>{exp.state}</td>
              <td>
                {canManage && exp.state === 'draft' && (
                  <>
                    <button onClick={() => validateExpenseMutation.mutate(exp.id)}>Valider</button>
                    <button onClick={() => cancelExpenseMutation.mutate(exp.id)}>Annuler</button>
                  </>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {canOperate && (
        <form className="inline-form" onSubmit={submitExpense}>
          <h2>Nouvelle depense</h2>
          <input placeholder="Categorie" value={expenseCategory} onChange={(e) => setExpenseCategory(e.target.value)} required />
          <input
            type="number"
            placeholder="Montant"
            value={expenseAmount}
            onChange={(e) => setExpenseAmount(e.target.value)}
            required
          />
          <select value={expenseMethod} onChange={(e) => setExpenseMethod(e.target.value as PaymentMethod)}>
            <option value="especes">Especes</option>
            <option value="banque">Banque</option>
          </select>
          {expenseMethod === 'especes' && (
            <select value={expenseSessionId} onChange={(e) => setExpenseSessionId(e.target.value)} required>
              <option value="">Session de caisse</option>
              {openSessions.map((s) => (
                <option key={s.id} value={s.id}>
                  Caisse #{s.register_id} (session {s.id})
                </option>
              ))}
            </select>
          )}
          <button type="submit" disabled={createExpenseMutation.isPending}>
            Enregistrer
          </button>
        </form>
      )}
    </div>
  )
}
