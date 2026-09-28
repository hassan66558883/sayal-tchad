export default function ProgressBar({ percent }: { percent: number | null }) {
  if (percent === null) {
    return <span style={{ color: 'var(--text-muted)' }}>-</span>
  }
  const clamped = Math.max(0, Math.min(100, percent))
  const tone = percent >= 100 ? 'success' : percent >= 60 ? '' : 'warning'
  return (
    <div className="progress">
      <div className="progress-track">
        <div className={`progress-fill ${tone}`} style={{ width: `${clamped}%` }} />
      </div>
      <span className="progress-label">{percent.toFixed(1)}%</span>
    </div>
  )
}
