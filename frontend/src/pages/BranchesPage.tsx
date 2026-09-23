import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { createBranch, listBranches } from '../api/branches'
import { useAuth } from '../auth/AuthContext'

export default function BranchesPage() {
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const { data: branches, isLoading, error } = useQuery({ queryKey: ['branches'], queryFn: listBranches })

  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: createBranch,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branches'] })
      setName('')
      setCode('')
      setFormError(null)
    },
    onError: () => setFormError("Impossible de creer l'agence (code deja utilise ?)."),
  })

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    mutation.mutate({ name, code })
  }

  return (
    <div>
      <h1>Agences</h1>
      {isLoading && <p>Chargement...</p>}
      {error && <p className="error">Erreur de chargement.</p>}
      <table className="data-table">
        <thead>
          <tr>
            <th>Code</th>
            <th>Nom</th>
            <th>Ville</th>
            <th>Telephone</th>
          </tr>
        </thead>
        <tbody>
          {branches?.map((b) => (
            <tr key={b.id}>
              <td>{b.code}</td>
              <td>{b.name}</td>
              <td>{b.city ?? '-'}</td>
              <td>{b.phone ?? '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {hasRole('direction_generale') && (
        <form className="inline-form" onSubmit={handleSubmit}>
          <h2>Nouvelle agence</h2>
          <input placeholder="Nom" value={name} onChange={(e) => setName(e.target.value)} required />
          <input placeholder="Code" value={code} onChange={(e) => setCode(e.target.value)} required />
          <button type="submit" disabled={mutation.isPending}>
            Creer
          </button>
          {formError && <p className="error">{formError}</p>}
        </form>
      )}
    </div>
  )
}
