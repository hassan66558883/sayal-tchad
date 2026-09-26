import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { createBankAccount, createBankTransaction, listBankAccounts, listBankTransactions } from '../api/finance'
import { useAuth } from '../auth/AuthContext'

export default function BankAccountsPage() {
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const canManage = hasRole('comptable')

  const { data: accounts } = useQuery({ queryKey: ['bank-accounts'], queryFn: listBankAccounts })
  const { data: transactions } = useQuery({ queryKey: ['bank-transactions'], queryFn: listBankTransactions })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['bank-accounts'] })
    queryClient.invalidateQueries({ queryKey: ['bank-transactions'] })
  }
  const createAccountMutation = useMutation({ mutationFn: createBankAccount, onSuccess: invalidate })
  const createTransactionMutation = useMutation({ mutationFn: createBankTransaction, onSuccess: invalidate })

  const [name, setName] = useState('')
  const [bankName, setBankName] = useState('')
  const [accountNumber, setAccountNumber] = useState('')
  const [openingBalance, setOpeningBalance] = useState('0')

  const [txAccountId, setTxAccountId] = useState('')
  const [txType, setTxType] = useState<'in' | 'out'>('in')
  const [txAmount, setTxAmount] = useState('')
  const [txReason, setTxReason] = useState('')

  function submitAccount(e: FormEvent) {
    e.preventDefault()
    createAccountMutation.mutate({
      name,
      bank_name: bankName,
      account_number: accountNumber,
      opening_balance: Number(openingBalance || 0),
    })
    setName('')
    setBankName('')
    setAccountNumber('')
    setOpeningBalance('0')
  }

  function submitTransaction(e: FormEvent) {
    e.preventDefault()
    if (!txAccountId || !txAmount) return
    createTransactionMutation.mutate({
      bank_account_id: Number(txAccountId),
      movement_type: txType,
      amount: Number(txAmount),
      reason: txReason || undefined,
      transaction_date: new Date().toISOString().slice(0, 10),
    })
    setTxAmount('')
    setTxReason('')
  }

  return (
    <div>
      <h1>Banque</h1>
      <table className="data-table">
        <thead>
          <tr>
            <th>Nom</th>
            <th>Banque</th>
            <th>Numero de compte</th>
            <th>Solde</th>
          </tr>
        </thead>
        <tbody>
          {accounts?.map((a) => (
            <tr key={a.id}>
              <td>{a.name}</td>
              <td>{a.bank_name}</td>
              <td>{a.account_number}</td>
              <td>{a.balance}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {canManage && (
        <form className="inline-form" onSubmit={submitAccount}>
          <h2>Nouveau compte bancaire</h2>
          <input placeholder="Nom" value={name} onChange={(e) => setName(e.target.value)} required />
          <input placeholder="Banque" value={bankName} onChange={(e) => setBankName(e.target.value)} required />
          <input
            placeholder="Numero de compte"
            value={accountNumber}
            onChange={(e) => setAccountNumber(e.target.value)}
            required
          />
          <input
            type="number"
            placeholder="Solde initial"
            value={openingBalance}
            onChange={(e) => setOpeningBalance(e.target.value)}
          />
          <button type="submit" disabled={createAccountMutation.isPending}>
            Creer
          </button>
        </form>
      )}

      <h2>Mouvements bancaires manuels</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>Compte</th>
            <th>Type</th>
            <th>Montant</th>
            <th>Motif</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          {transactions?.map((t) => (
            <tr key={t.id}>
              <td>{accounts?.find((a) => a.id === t.bank_account_id)?.name ?? t.bank_account_id}</td>
              <td>{t.movement_type === 'in' ? 'Entree' : 'Sortie'}</td>
              <td>{t.amount}</td>
              <td>{t.reason ?? '-'}</td>
              <td>{t.transaction_date}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {canManage && (
        <form className="inline-form" onSubmit={submitTransaction}>
          <h2>Nouveau mouvement</h2>
          <select value={txAccountId} onChange={(e) => setTxAccountId(e.target.value)} required>
            <option value="">Compte</option>
            {accounts?.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
          <select value={txType} onChange={(e) => setTxType(e.target.value as 'in' | 'out')}>
            <option value="in">Entree</option>
            <option value="out">Sortie</option>
          </select>
          <input type="number" placeholder="Montant" value={txAmount} onChange={(e) => setTxAmount(e.target.value)} required />
          <input placeholder="Motif" value={txReason} onChange={(e) => setTxReason(e.target.value)} />
          <button type="submit" disabled={createTransactionMutation.isPending}>
            Enregistrer
          </button>
        </form>
      )}
    </div>
  )
}
