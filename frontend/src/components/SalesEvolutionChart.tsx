import type { SalesEvolutionPoint } from '../api/dashboard'

const WIDTH = 640
const HEIGHT = 220
const PAD_LEFT = 56
const PAD_BOTTOM = 28
const PAD_TOP = 16
const PAD_RIGHT = 16

function niceMax(value: number): number {
  if (value <= 0) return 100
  const magnitude = Math.pow(10, Math.floor(Math.log10(value)))
  const normalized = value / magnitude
  const step = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10
  return step * magnitude
}

export default function SalesEvolutionChart({ data }: { data: SalesEvolutionPoint[] }) {
  if (data.length === 0) {
    return <p style={{ color: 'var(--text-muted)' }}>Aucune donnee pour cette periode.</p>
  }

  const plotW = WIDTH - PAD_LEFT - PAD_RIGHT
  const plotH = HEIGHT - PAD_TOP - PAD_BOTTOM
  const maxValue = niceMax(Math.max(...data.map((d) => d.invoiced_total)))
  const stepX = data.length > 1 ? plotW / (data.length - 1) : 0

  const points = data.map((d, i) => {
    const x = PAD_LEFT + (data.length > 1 ? i * stepX : plotW / 2)
    const y = PAD_TOP + plotH - (d.invoiced_total / maxValue) * plotH
    return { x, y, d }
  })

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')
  const areaPath = `${linePath} L${points[points.length - 1].x.toFixed(1)},${PAD_TOP + plotH} L${points[0].x.toFixed(1)},${PAD_TOP + plotH} Z`

  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((f) => Math.round(maxValue * f))
  const last = points[points.length - 1]
  const labelStep = Math.max(1, Math.ceil(data.length / 6))

  return (
    <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} width="100%" height={HEIGHT} role="img" aria-label="Evolution des ventes">
      {yTicks.map((tick) => {
        const y = PAD_TOP + plotH - (tick / maxValue) * plotH
        return (
          <g key={tick}>
            <line x1={PAD_LEFT} x2={WIDTH - PAD_RIGHT} y1={y} y2={y} stroke="var(--border)" strokeWidth={1} />
            <text x={PAD_LEFT - 8} y={y + 4} textAnchor="end" fontSize={10} fill="var(--text-muted)">
              {tick >= 1000 ? `${Math.round(tick / 1000)}k` : tick}
            </text>
          </g>
        )
      })}

      {points.map(
        (p, i) =>
          i % labelStep === 0 && (
            <text key={`x-${i}`} x={p.x} y={HEIGHT - 6} textAnchor="middle" fontSize={10} fill="var(--text-muted)">
              {p.d.period.slice(5)}
            </text>
          ),
      )}

      <path d={areaPath} fill="var(--accent)" opacity={0.1} stroke="none" />
      <path d={linePath} fill="none" stroke="var(--accent)" strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />

      {points.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r={4} fill="var(--accent)" stroke="var(--panel-bg)" strokeWidth={2}>
          <title>
            {p.d.period}: {p.d.invoiced_total.toLocaleString('fr-FR')} FCFA ({p.d.invoice_count} facture
            {p.d.invoice_count > 1 ? 's' : ''})
          </title>
        </circle>
      ))}

      <text x={last.x} y={last.y - 10} textAnchor="end" fontSize={11} fontWeight={700} fill="var(--text-h)">
        {last.d.invoiced_total.toLocaleString('fr-FR')}
      </text>
    </svg>
  )
}
