import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import {
  createProduct,
  createProductCategory,
  createUom,
  createUomCategory,
  listProductCategories,
  listProducts,
  listUoms,
  listUomCategories,
} from '../api/products'
import { useAuth } from '../auth/AuthContext'

export default function ProductsPage() {
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const canManage = hasRole('achats', 'stock')

  const { data: products } = useQuery({ queryKey: ['products'], queryFn: listProducts })
  const { data: categories } = useQuery({ queryKey: ['product-categories'], queryFn: listProductCategories })
  const { data: uoms } = useQuery({ queryKey: ['uoms'], queryFn: listUoms })
  const { data: uomCategories } = useQuery({ queryKey: ['uom-categories'], queryFn: listUomCategories })

  const [name, setName] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [uomId, setUomId] = useState('')
  const [salePrice, setSalePrice] = useState('')
  const [error, setError] = useState<string | null>(null)

  const productMutation = useMutation({
    mutationFn: createProduct,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
      setName('')
      setSalePrice('')
      setError(null)
    },
    onError: () => setError('Impossible de creer ce produit (code-barres deja utilise ?).'),
  })

  const [categoryName, setCategoryName] = useState('')
  const [categoryCode, setCategoryCode] = useState('')
  const categoryMutation = useMutation({
    mutationFn: createProductCategory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['product-categories'] })
      setCategoryName('')
      setCategoryCode('')
    },
  })

  const [uomCategoryName, setUomCategoryName] = useState('')
  const uomCategoryMutation = useMutation({
    mutationFn: createUomCategory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['uom-categories'] })
      setUomCategoryName('')
    },
  })

  const [uomName, setUomName] = useState('')
  const [uomCategoryId, setUomCategoryId] = useState('')
  const [uomFactor, setUomFactor] = useState('1')
  const [uomIsReference, setUomIsReference] = useState(false)
  const uomMutation = useMutation({
    mutationFn: createUom,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['uoms'] })
      setUomName('')
      setUomFactor('1')
      setUomIsReference(false)
    },
  })

  function handleCreateProduct(e: FormEvent) {
    e.preventDefault()
    productMutation.mutate({
      name,
      category_id: categoryId ? Number(categoryId) : undefined,
      uom_id: Number(uomId),
      sale_price: salePrice ? Number(salePrice) : undefined,
    })
  }

  return (
    <div>
      <h1>Produits</h1>
      <table className="data-table">
        <thead>
          <tr>
            <th>Reference</th>
            <th>Nom</th>
            <th>Prix de vente</th>
            <th>Stock min.</th>
          </tr>
        </thead>
        <tbody>
          {products?.map((p) => (
            <tr key={p.id}>
              <td>{p.reference}</td>
              <td>{p.name}</td>
              <td>{p.sale_price}</td>
              <td>{p.min_stock_qty}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {canManage && (
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
          <form className="inline-form" onSubmit={handleCreateProduct}>
            <h2>Nouveau produit</h2>
            <input placeholder="Nom" value={name} onChange={(e) => setName(e.target.value)} required />
            <select value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
              <option value="">Categorie (optionnel)</option>
              {categories?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
            <select value={uomId} onChange={(e) => setUomId(e.target.value)} required>
              <option value="">Unite de stockage</option>
              {uoms?.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.name}
                </option>
              ))}
            </select>
            <input
              placeholder="Prix de vente"
              type="number"
              value={salePrice}
              onChange={(e) => setSalePrice(e.target.value)}
            />
            <button type="submit" disabled={productMutation.isPending}>
              Creer
            </button>
            {error && <p className="error">{error}</p>}
          </form>

          <form
            className="inline-form"
            onSubmit={(e) => {
              e.preventDefault()
              categoryMutation.mutate({ name: categoryName, code: categoryCode })
            }}
          >
            <h2>Nouvelle categorie</h2>
            <input placeholder="Nom" value={categoryName} onChange={(e) => setCategoryName(e.target.value)} required />
            <input placeholder="Code" value={categoryCode} onChange={(e) => setCategoryCode(e.target.value)} required />
            <button type="submit">Creer</button>
          </form>

          <form
            className="inline-form"
            onSubmit={(e) => {
              e.preventDefault()
              uomCategoryMutation.mutate({ name: uomCategoryName })
            }}
          >
            <h2>Nouvelle categorie d'unite</h2>
            <input
              placeholder="Nom (ex: Poids)"
              value={uomCategoryName}
              onChange={(e) => setUomCategoryName(e.target.value)}
              required
            />
            <button type="submit">Creer</button>
          </form>

          <form
            className="inline-form"
            onSubmit={(e) => {
              e.preventDefault()
              uomMutation.mutate({
                name: uomName,
                category_id: Number(uomCategoryId),
                factor: Number(uomFactor),
                is_reference: uomIsReference,
              })
            }}
          >
            <h2>Nouvelle unite</h2>
            <input placeholder="Nom (ex: Sac de 50 kg)" value={uomName} onChange={(e) => setUomName(e.target.value)} required />
            <select value={uomCategoryId} onChange={(e) => setUomCategoryId(e.target.value)} required>
              <option value="">Categorie d'unite</option>
              {uomCategories?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
            <input
              placeholder="Facteur (relatif a l'unite de reference)"
              type="number"
              step="0.01"
              value={uomFactor}
              onChange={(e) => setUomFactor(e.target.value)}
              required
            />
            <label>
              <input type="checkbox" checked={uomIsReference} onChange={(e) => setUomIsReference(e.target.checked)} />
              Unite de reference de la categorie
            </label>
            <button type="submit">Creer</button>
          </form>
        </div>
      )}
    </div>
  )
}
